
import logging

import boto3
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import requests
import json
from botocore.exceptions import ClientError
from celery import shared_task
from io import BytesIO
from customer.models import OrderItem, Invoice, Customer, Order
from product.models import Product
from user.models import DELIVERY_CHOICES, AppConfigData
from django.http import HttpResponse
from django.conf import settings


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

@shared_task
def deliver_email(pdf, customer_email, shop_email, pdf_name):
    from user.models import AppConfigData
    USERNAME_SMTP = AppConfigData.objects.get(key='USERNAME_SMTP').value
    PASSWORD_SMTP = AppConfigData.objects.get(key='PASSWORD_SMTP').value
    # applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
    SENDER = 'townie.store@gmail.com'
    SENDERNAME = 'Townie'
    USERNAME_SMTP = USERNAME_SMTP
    PASSWORD_SMTP = PASSWORD_SMTP
    HOST = "email-smtp.us-east-2.amazonaws.com"
    PORT = 587
    SUBJECT = 'Townie Invoice'
    msg = MIMEMultipart()
    to = ', '.join([customer_email, shop_email])
    msg['Subject'] = SUBJECT
    msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
    msg['To'] = to
    part1 = MIMEText('Test', 'plain')
    msg.attach(part1)
    part = MIMEApplication(pdf)
    part.add_header('Content-Disposition', 'attachment', filename=pdf_name)
    msg.attach(part)
    # part2 = MIMEText(BODY_HTML, 'html')
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.ehlo()
        server.starttls()
        # stmplib docs recommend calling ehlo() before & after starttls()
        server.ehlo()
        server.login(USERNAME_SMTP, PASSWORD_SMTP)

        print(to)
        server.sendmail(SENDER, to, msg.as_string())
        server.close()
    # Display an error message if something goes wrong.
    except Exception as e:
        db_logger.exception(e)
    else:
        db_logger.info("email sent to {0} - {1}".format(customer_email, shop_email))
        print("Email sent!")


@shared_task()
def delivery_system_call(**data):
    try:
        response = requests.post('https://api.townie.in/delivery/v1/assignorder', data=json.dumps(data),
                                 headers={'content-type': 'application/json'})
        db_logger.debug('Delivery boy response : {0} => {1}'.format(response.content, str(data)))
    except Exception as e:
        db_logger.exception(e)


@shared_task()
def render_to_pdf(delivery_type, customer, order, delivery_charge):
    try:
        customer = Customer.objects.get(id=customer)
        order = Order.objects.get(id=order)
        gst_number = order.shop.gst_reg_number
        pan_number = gst_number[2:12]
        billing_address = customer.customer_addresses.filter(is_deleted=False).last().address
        shipping_address = customer.customer_addresses.filter(is_deleted=False).last().address
        vendor_address = order.shop.address
        sold_by = vendor_address
        order_id = order.id
        customer_email = customer.user.email
        shop_email = order.shop.user.email
        invoice = Invoice.objects.filter(shop=order.shop)
        if invoice:
            invoice_number = invoice.last().invoice_id + 1
            created_at = invoice.last().created_at
            Invoice.objects.create(invoice_id=invoice_number, shop=order.shop, order=order)
        else:
            invoice_number = 1
            invoice = Invoice.objects.create(invoice_id=invoice_number, shop=order.shop, order=order)
            created_at = invoice.created_at
        # amount_words = convert_to_words()
        order_items = order.order_items.all()
        product_details = []
        igst = 0
        cgst = 0
        sgst = 0
        kfc = 0
        grand_sum = grand_total = 0
        for value in order_items:
            x = value.product_id.mrp
            print(value.product_id)
            tax_rate = int(value.product_id.tax_rate)
            if tax_rate == 5:
                y = (100 * x) / 105
                cgst = 0.0238095238 * x
                sgst = 0.0238095238 * x
            elif tax_rate == 12:
                y = (100 * x) / 113
                kfc = y / 100
                cgst = (0.1150442478 * x - kfc) / 2
                sgst = (0.1150442478 * x - kfc) / 2

            elif tax_rate == 18:
                y = 100 * x / 119
                kfc = y / 100
                cgst = (0.1596638655 * x - kfc) / 2
                sgst = (0.1596638655 * x - kfc) / 2

            elif tax_rate == 28:
                y = 100 * x / 129
                kfc = y / 100
                cgst = (0.2248062016 * x - kfc) / 2
                sgst = (0.2248062016 * x - kfc) / 2
            grand_total = value.total + cgst + sgst + kfc
            grand_sum += grand_total
            product_details.append({'name': value.product_id.name, 'quantity': value.quantity, 'unit_prize': value.rate,
                                    'total': value.total, 'cgst': round(cgst, 2),'sgst': round(sgst, 2),
                                    'igst': round(igst, 2), 'kfc': round(kfc, 2),
                                    'grand_total': grand_total})
        if delivery_type == DELIVERY_CHOICES.pickup:
            product_details = product_details
        elif delivery_type == DELIVERY_CHOICES.self_delivery or delivery_type == DELIVERY_CHOICES.bulk_delivery:
            x = delivery_charge
            y = 100 * x / 129
            kfc = y / 100
            cgst = (0.2248062016 * x - kfc) / 2
            sgst = (0.2248062016 * x - kfc) / 2
            grand_total = x + cgst + sgst + kfc
            product_details.append({'name': 'Delivery charge', 'quantity': 1, 'unit_prize': x,
                                    'total': x, 'cgst': round(cgst, 2),'sgst': round(sgst, 2),
                                    'igst': round(igst, 2), 'kfc': round(kfc, 2),
                                    'grand_total': grand_total})
            product_details = product_details
            grand_sum += grand_total

        elif delivery_type == DELIVERY_CHOICES.townie_ship:
            invoice = invoice.last()
            townie_invoice_id = invoice.townie_invoice_id +1
            invoice.townie_invoice_id = townie_invoice_id
            invoice.save()
            townie_referal = AppConfigData.objects.get(key='TOWNIE_REFERRAL_PERCENTAGE').value
            townie_referal = float(townie_referal) / 100
            referal_fee = townie_referal * order.grand_total * 1.18
            tsf = 0.0236 * order.grand_total
            x = referal_fee + tsf
            y = 100 * x / 129
            kfc = y / 100
            cgst = (0.2248062016 * x - kfc) / 2
            sgst = (0.2248062016 * x - kfc) / 2
            grand_total = x + cgst + sgst + kfc
            townie_details = []
            townie_details.append({'name': 'Service charge', 'quantity': 1, 'unit_prize': x,
                                   'total': x, 'cgst': round(cgst, 2), 'sgst': round(sgst, 2),
                                   'igst': round(igst, 2), 'kfc': round(kfc, 2),
                                   'grand_total': grand_total})
            context = {
                "invoice": townie_invoice_id,
                "billing_address": billing_address,
                "shipping_address": billing_address,
                "order_no": order_id,
                "order_date": order.created_at,
                "invoice_date": created_at,
                "amount_words": "",
                "pan_no": pan_number,
                "gst_no": gst_number,
                "product_details": townie_details,
                # "vendor_address": vendor_address,
                "sold_by": 'Townie'
            }
            delivery_details = order.shop.shop_delivery_options.last()
            if delivery_details.free_delivery_for:
                if float(grand_total) > delivery_details.free_delivery_for:
                    product_details = product_details

            else:
                x = delivery_charge
                y = 100 * x / 129
                kfc = y / 100
                cgst = (0.2248062016 * x - kfc) / 2
                sgst = (0.2248062016 * x - kfc) / 2
                grand_total = x + cgst + sgst + kfc
                product_details.append({'name': 'Delivery charge', 'quantity': 1, 'unit_prize': x,
                                        'total': x, 'cgst': round(cgst, 2), 'sgst': round(sgst, 2),
                                        'igst': round(igst, 2), 'kfc': round(kfc,2 ),
                                        'grand_total': grand_total})
                product_details = product_details
                grand_sum += grand_total
            try:
                template = get_template('townie_Invoice.html')
                html = template.render(context)
                file = open(settings.MEDIA_ROOT + str(townie_invoice_id) + '.pdf', "w+b")
                pisaStatus = pisa.CreatePDF(html.encode('utf-8'), dest=file,
                                            encoding='utf-8')
                file.seek(0)
                pdf = file.read()
                SENDER = 'townie.store@gmail.com'
                deliver_email.apply_async(queue='normal', args=(pdf,
                                                                SENDER,
                                                                shop_email,
                                                                str(townie_invoice_id) + '.pdf'))
                file.close()
            except Exception as e:
                db_logger.exception(e)
            x = delivery_charge
            y = 100 * x / 129
            kfc = y / 100
            cgst = (0.2248062016 * x - kfc) / 2
            sgst = (0.2248062016 * x - kfc) / 2
            grand_total = x + cgst + sgst + kfc
            product_details.append({'name': 'Delivery charge', 'quantity': 1, 'unit_prize': x,
                                    'total': x, 'cgst': round(cgst, 2), 'sgst': round(sgst, 2),
                                    'igst': round(igst, 2), 'kfc': round(kfc,2 ),
                                    'grand_total': grand_total})
            product_details = product_details
            grand_sum += grand_total
        context = {
            "invoice": invoice_number,
            "billing_address": billing_address,
            "shipping_address": shipping_address,
            "order_no": order_id,
            "order_date": order.created_at,
            "invoice_date": created_at,
            "amount_words": "",
            "pan_no": pan_number,
            "gst_no": gst_number,
            "product_details": product_details,
            "vendor_address": vendor_address,
            "sold_by": sold_by
        }

        template = get_template('townie_Invoice.html')
        html = template.render(context)
        file = open(settings.MEDIA_ROOT + str(invoice_number) + '.pdf', "w+b")
        pisaStatus = pisa.CreatePDF(html.encode('utf-8'), dest=file,
                                    encoding='utf-8')
        file.seek(0)
        pdf = file.read()
        deliver_email.apply_async(queue='normal', args=(pdf,
                                                        customer_email,
                                                        shop_email,
                                                        str(invoice_number) + '.pdf'))
        # deliver_email(pdf, customer_email, shop_email, str(invoice_number) + '.pdf')
        file.close()
        return HttpResponse(pdf, 'application/pdf')
        # result = BytesIO()
        # pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        # if not pdf.err:
        #     # pass
            # deliver_email(email)
        #     return HttpResponse(result.getvalue(), content_type='application/pdf')
        # return None
    except Exception as e:
        print(e)
        db_logger.exception(e)

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

            print(e)
            db_logger.exception(e)

