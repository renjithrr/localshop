
import logging

import boto3

import requests
import json
from botocore.exceptions import ClientError
from celery import shared_task
from io import BytesIO
from customer.models import OrderItem

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


@shared_task
def deliver_email(email_id):
    from user.models import AppConfigData
    aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
    aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
    applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
    SENDER = AppConfigData.objects.get(key='SENDER').value
    AWS_REGION = "ap-south-1"
    SUBJECT = 'Townie Invoice'
    CHARSET = "UTF-8"
    client = boto3.client('pinpoint',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=AWS_REGION)
    try:
        response = client.send_messages(
            ApplicationId=applicationId,
            MessageRequest={
                'Addresses': {
                    email_id: {
                        'ChannelType': 'EMAIL'
                    }
                },
                'MessageConfiguration': {
                    'EmailMessage': {
                        'FromAddress': SENDER,
                        'SimpleEmail': {
                            'Subject': {
                                'Charset': CHARSET,
                                'Data': SUBJECT
                            },
                            # 'HtmlPart': {
                            #     'Charset': CHARSET,
                            #     'Data': BODY_HTML
                            # },
                            'TextPart': {
                                'Charset': CHARSET,
                                'Data': 'test'
                            }
                        }
                    }
                }
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print(response)


@shared_task()
def delivery_system_call(**data):
    response = requests.post('https://townie.in/delivery/v1/assignorder', data=json.dumps(data),
                             headers={'content-type': 'application/json'})
    db_logger.debug('Delivery boy response : {0} => {1}'.format(response.content, str(data)))


# def render_to_pdf(template_src, context_dict):

@shared_task()
def render_to_pdf(template_src, email, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        pass
        deliver_email(email)
        # return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@shared_task()
def manage_product_quantity(order_id):
    from product.models import Product
    items = OrderItem.objects.filter(order_id=order_id)
    for value in items:
        try:
            product = Product.objects.get(id=value.product_id.id)
            db_logger.debug('before quantity + product id : {0} => {1}'.format(product.quantity, product.id))
            product.quantity = product.quantity - value.quantity
            product.save()
            db_logger.debug('after quantity: {0}'.format(product.quantity))
        except Exception as e:
            db_logger.exception(e)

