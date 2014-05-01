
from types import DictionaryType, ListType

from django_ses import SESBackend
from django.core.mail import EmailMessage
from django.conf import settings


def send_simple_email(subject, body, recipients, headers=None):
    """ Send emails for many purposes
    """
    sender = settings.DEFAULT_FROM_EMAIL

    if headers is not None and isinstance(headers, DictionaryType):
        headers = headers
    else:
        # default
        headers = {'Reply-To': settings.AWS_SES_RETURN_PATH}

    assert isinstance(recipients, ListType)
    recipients = recipients

    message = EmailMessage(subject, body,
                           sender, recipients,
                           headers = headers)
    sender = SESBackend()
    result = sender.send_messages([message])

    return result