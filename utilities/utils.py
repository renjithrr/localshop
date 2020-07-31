import math, random
import boto3
import xlwt

from collections import defaultdict
from django.apps import apps
from django.http import HttpResponse



class Kw:
    def __init__(self, label=None, **kwargs):
        assert (len(kwargs) == 1)
        for k, v in kwargs.items():
            self.id = k
            self.v = v
        self.label = label or self.id


class Konstants:
    def __init__(self, *args):
        self.klist = args
        for k in self.klist:
            setattr(self, k.id, k.v)

    def choices(self):
        return [(k.v, k.label) for k in self.klist]

    def get_label(self, key):
        for k in self.klist:
            if k.v == key:
                return k.label
        return None


def OTPgenerator() :
    digits_in_otp = "0123456789"
    OTP = ""

# for a 4 digit OTP we are using 4 in range
    for i in range(6) :
        OTP += digits_in_otp[math.floor(random.random() * 10)]

    return OTP



class BulkCreateManager(object):
    """
    This helper class keeps track of ORM objects to be created for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is created for all models.
    """

    def __init__(self, chunk_size=100):
        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        """
        Add an object to the queue to be created, and call bulk_create if we
        have enough objs.
        """
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        """
        Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))


def deliver_sms(mobile_number, otp):
    from user.models import AppConfigData
    aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
    aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
    applicationId = AppConfigData.objects.get(key='APPLICATION_ID').value
    client = boto3.client(
        "pinpoint",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="us-east-1"
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
                        'OriginationNumber': "+12515453033",
                        'SenderId': "Townie"
                    }
                }
            })
        print(response)

    except Exception as e:
        pass
    return True


def download_excel_data(shop):
    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')

    #decide file name
    response['Content-Disposition'] = 'attachment; filename="product_upload.xls"'

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    #adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True

    #column header names, you can use your own headers here
    columns = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'mrp', 'offer_prize',
               'lowest_selling_rate', 'highest_selling_rate', 'product_code', 'tax_rate', 'moq', 'unit']

    #write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #get your data, from database or from a text file...
    data = shop.shop_products.all() #dummy method to fetch data.
    print(data)
    for my_row in data:
        row_num = row_num + 1
        print(row_num)
        ws.write(row_num, 0, my_row.name, font_style)
        ws.write(row_num, 1, my_row.category.name, font_style)
        ws.write(row_num, 2, my_row.size, font_style)
        ws.write(row_num, 3, my_row.color, font_style)
        ws.write(row_num, 4, my_row.quantity, font_style)
        ws.write(row_num, 5, my_row.description, font_style)
        ws.write(row_num, 6, my_row.brand, font_style)
        ws.write(row_num, 7, my_row.mrp, font_style)
        ws.write(row_num, 8, my_row.offer_prize, font_style)
        ws.write(row_num, 9, my_row.lowest_selling_rate, font_style)
        ws.write(row_num, 10, my_row.highest_selling_rate, font_style)
        ws.write(row_num, 11, my_row.product_id, font_style)
        ws.write(row_num, 12, my_row.tax_rate, font_style)
        ws.write(row_num, 13, my_row.moq, font_style)
        ws.write(row_num, 14, my_row.unit, font_style)


    wb.save(response)
    return response
