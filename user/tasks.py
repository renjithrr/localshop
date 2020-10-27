
import logging

import boto3
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import json
from botocore.exceptions import ClientError
from celery import shared_task
from io import BytesIO
from customer.models import OrderItem, Invoice
from user.models import DELIVERY_CHOICES

from xhtml2pdf import pisa
from django.template.loader import get_template

db_logger = logging.getLogger('db')


@shared_task
def deliver_sms(mobile_number, otp):
    from user.models import AppConfigData
    aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
    aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
    applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
    client = boto3.client(
        "pinpoint",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="ap-south-1"
    )
    try:
        response = client.send_messages(
            ApplicationId=applicationId,
            MessageRequest={
                'Addresses': {
                    mobile_number: {
                        'ChannelType': 'SMS'
                    }
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': 'Townie verification otp is ' + otp,
                        'Keyword': "keyword_555701130102",
                        'MessageType': "TRANSACTIONAL",
                        'OriginationNumber': "+13474275421",
                        'SenderId': "Townie"
                    }
                }
            })
        db_logger.debug('pinpoint sms to : {0} => {1}'.format(mobile_number, str(response)))
    except Exception as e:
        print(e)
        db_logger.exception(e)
    return True


# @shared_task
# def deliver_email(email_id):
#     from user.models import AppConfigData
#     aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
#     aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
#     applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
#     SENDER = AppConfigData.objects.get(key='SENDER').value
#     AWS_REGION = "ap-south-1"
#     SUBJECT = 'Townie Invoice'
#     CHARSET = "UTF-8"
#     client = boto3.client('pinpoint',
#                           aws_access_key_id=aws_access_key_id,
#                           aws_secret_access_key=aws_secret_access_key,
#                           region_name=AWS_REGION)
#     try:
#         response = client.send_messages(
#             ApplicationId=applicationId,
#             MessageRequest={
#                 'Addresses': {
#                     email_id: {
#                         'ChannelType': 'EMAIL'
#                     }
#                 },
#                 'MessageConfiguration': {
#                     'EmailMessage': {
#                         'FromAddress': SENDER,
#                         'SimpleEmail': {
#                             'Subject': {
#                                 'Charset': CHARSET,
#                                 'Data': SUBJECT
#                             },
#                             # 'HtmlPart': {
#                             #     'Charset': CHARSET,
#                             #     'Data': BODY_HTML
#                             # },
#                             'TextPart': {
#                                 'Charset': CHARSET,
#                                 'Data': 'test'
#                             }
#                         }
#                     }
#                 }
#             }
#         )
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#     else:
#         print(response)

# @shared_task
def deliver_email(email_id):
    from user.models import AppConfigData
    # aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
    # aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
    # applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
    SENDER = 'townie.store@gmail.com'
    SENDERNAME = 'Townie'
    USERNAME_SMTP = "AKIAYCYS6KN3IN26ZJIJ"
    PASSWORD_SMTP = "BKucBsmYcB/g+rcf78XqAEPbwqFg74sILvTpZxkB0fPc"
    HOST = "email-smtp.us-east-2.amazonaws.com"
    PORT = 587
    SUBJECT = 'Townie Invoice'
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
    msg['To'] = email_id
    part1 = MIMEText('Test', 'plain')
    msg.attach(part1)
    # part2 = MIMEText(BODY_HTML, 'html')
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.ehlo()
        server.starttls()
        # stmplib docs recommend calling ehlo() before & after starttls()
        server.ehlo()
        server.login(USERNAME_SMTP, PASSWORD_SMTP)
        server.sendmail(SENDER, email_id, msg.as_string())
        server.close()
    # Display an error message if something goes wrong.
    except Exception as e:
        print("Error: ", e)
    else:
        print("Email sent!")


@shared_task()
def delivery_system_call(**data):
    try:
        response = requests.post('https://townie.in/delivery/v1/assignorder', data=json.dumps(data),
                                 headers={'content-type': 'application/json'})
        db_logger.debug('Delivery boy response : {0} => {1}'.format(response.content, str(data)))
    except Exception as e:
        db_logger.exception(e)


# def render_to_pdf(template_src, context_dict):

# Python program to print a given number in
# words. The program handles numbers
# from 0 to 9999

# A function that prints
# given number in words
# def convert_to_words(num):
#     # Get number of digits
#     # in given number
#     l = len(num)
#
#     # Base cases
#     if (l == 0):
#         print("empty string")
#         return;
#
#     if (l > 4):
#         print("Length more than 4 is not supported")
#         return
#
#     # The first string is not used,
#     # it is to make array indexing simple
#     single_digits = ["zero", "one", "two", "three",
#                      "four", "five", "six", "seven",
#                      "eight", "nine"]
#
#     # The first string is not used,
#     # it is to make array indexing simple
#     two_digits = ["", "ten", "eleven", "twelve",
#                   "thirteen", "fourteen", "fifteen",
#                   "sixteen", "seventeen", "eighteen",
#                   "nineteen"]
#
#     # The first two string are not used,
#     # they are to make array indexing simple
#     tens_multiple = ["", "", "twenty", "thirty", "forty",
#                      "fifty", "sixty", "seventy", "eighty",
#                      "ninety"]
#
#     tens_power = ["hundred", "thousand"]
#
#     # Used for debugging purpose only
#     print(num, ":", end=" ")
#
#     # For single digit number
#     if (l == 1):
#         print(single_digits[ord(num[0]) - '0'])
#         return
#
#     # Iterate while num is not '\0'
#     x = 0
#     while (x < len(num)):
#
#         # Code path for first 2 digits
#         if (l >= 3):
#             if (ord(num[x]) - 48 != 0):
#                 print(single_digits[ord(num[x]) - 48],
#                       end=" ")
#                 print(tens_power[l - 3], end=" ")
#             # here len can be 3 or 4
#
#             l -= 1
#
#         # Code path for last 2 digits
#         else:
#
#             # Need to explicitly handle
#             # 10-19. Sum of the two digits
#             # is used as index of "two_digits"
#             # array of strings
#             if (ord(num[x]) - 48 == 1):
#                 sum = (ord(num[x]) - 48 +
#                        ord(num[x + 1]) - 48)
#                 print(two_digits[sum])
#                 return;
#
#             # Need to explicitely handle 20
#             elif (ord(num[x]) - 48 == 2 and
#                               ord(num[x + 1]) - 48 == 0):
#                 print("twenty")
#                 return;
#
#             # Rest of the two digit
#             # numbers i.e., 21 to 99
#             else:
#                 i = ord(num[x]) - 48
#                 if (i > 0):
#                     print(tens_multiple[i], end=" ")
#                 else:
#                     print("", end="")
#                 x += 1
#                 if (ord(num[x]) - 48 != 0):
#                     print(single_digits[ord(num[x]) - 48])
#         x += 1



# This code is contributed
# by Mithun Kumar

@shared_task()
def render_to_pdf(product, delivery_type, customer, order):
    # x = product.mrp
    # tax_rate = int(product.tax_rate)
    # if tax_rate == 5:
    #     y = (100 * x)/105
    #     cgst = 0.0238095238 * x
    #     sgst = 0.0238095238 * x
    # elif tax_rate == 12:
    #     y = (100 * x)/113
    #     kfc = y/100
    #     cgst = (0.1150442478 *x - kfc) / 2
    #     sgst = (0.1150442478 *x - kfc) / 2
    #
    # elif tax_rate == 18:
    #     y = 100 * x/119
    #     kfc = y/100
    #     cgst = (0.1596638655 *x - kfc) / 2
    #     sgst = (0.1596638655 *x - kfc) / 2
    #
    # elif tax_rate == 28:
    #     y = 100 * x/129
    #     kfc = y/100
    #     cgst = (0.2248062016 *x - kfc) / 2
    #     sgst = (0.2248062016 *x - kfc) / 2
    #
    #
    # gst_number = product.shop.gst_reg_number
    # pan_number = gst_number[2:12]
    # billing_address = customer.customer_addresses.filter(is_deleted=False).last()
    # shipping_address = customer.customer_addresses.filter(is_deleted=False).last()
    # vendor_address = order.shop.address
    # order_id = order.id
    # invoice = Invoice.objects.filter(shop=order.shop)
    # # amount_words = convert_to_words()
    # if delivery_type == DELIVERY_CHOICES.self_delivery:
    #     pass
    # if invoice:
    #     invoice_number = invoice.last().invoice_id + 1
    #     Invoice.objects.create(invoice_id=invoice_number, shop=order.shop, order=order)
    # else:
    #     invoice_number = 1
    #     Invoice.objects.create(invoice_id=invoice_number, shop=order.shop, order=order)
    # template = get_template(template_src)
    # html = template.render(context_dict)
    # result = BytesIO()
    # pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    # if not pdf.err:
    #     pass
    #     deliver_email(email)
        # return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@shared_task()
def manage_product_quantity(order_id):
    from product.models import Product
    items = OrderItem.objects.filter(order_id=order_id)
    for value in items:
        try:
            product = Product.objects.get(id=value.product_id.id)
            # db_logger.debug('before quantity + product id : {0} => {1}'.format(product.quantity, product.id))
            product.quantity = product.quantity - value.quantity
            product.save()
            # db_logger.debug('after quantity: {0}'.format(product.quantity))
        except Exception as e:
            db_logger.exception(e)

