__author__ = 'horacioibrahim'

import json

from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings


def zero_hour_tomorrow():
    """
    Return zero hour of next day
    """
    today = timezone.now()
    zero_hour_today = datetime.combine(today, datetime.min.time())
    tomorrow = zero_hour_today + timedelta(days=1)

    return tomorrow


def is_json(json_data):

    try:
        res_json = json.loads(json_data)
    except ValueError, e:
        return False
    return True

def upload_image_handler(f):
    # Save to path MEDIA_ROOT
    image_to_save = os.path.join(settings.MEDIA_ROOT, f.name)
    with open(image_to_save, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    image_url_relative = ''.join([settings.MEDIA_URL,
                                  os.path.basename(destination.name)])
    return image_url_relative

