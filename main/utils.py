

import os
from urlparse import urlparse
from types import DictionaryType, ListType
from httplib import HTTPSConnection, CannotSendRequest, BadStatusLine
from urllib import urlencode
from json import load as json_load

from django_ses import SESBackend
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.translation import ugettext as _


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

def relative_path_url(url):
    o = urlparse(url)
    return o.path


class FacebookAPIRequests(object):

    """
    All request to API pass by here. Use the HTTP verbs for each request. For
    each method (get, post, put and delete) is need an URN and a list of fields
    its passed as list of tuples that is encoded by urlencode (e.g:
    [("field_api", "value")]

    endpoint: is relative path of URL https://graph.facebook.com/endpoint?k=v
    where endpoint is "/endpoint?"

    All methods appends an api_token that is encoded in url params. The
    api_token is given in config.py its useful to work in sandbox mode.

    :method get: make a GET request
    :method post: make a POST request
    :method put: make a PUT request
    :method delete: make a DELETE request
    """
    APP_SECRET = settings.FACEBOOK_API['app_secret']
    APP_ID = settings.FACEBOOK_API['app_id']
    API_HOSTANME = 'graph.facebook.com'

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    __conn = HTTPSConnection(API_HOSTANME) # not put in instance
    __conn.timeout = 10

    def __init__(self, **options):
        debug_level = options.get('debug_level', 0)
        self.__conn.set_debuglevel(debug_level)
        self.ACCESS_TOKEN = "|".join([self.APP_ID, self.APP_SECRET])
        self.user_access_token = options.get('user_access_token', None)

    def __validation(self, response, msg=None):
        """
        Validates if data returned by API contains errors json.
        """
        errors = None
        try:
            results = json_load(response)
        except:
            raise TypeError("Validation errors.")

        errors = results.get('error', None)
        if errors:
            raise TypeError(_(errors['message']))

        return results

    def __reload_conn(self):
        """
        Wrapper to keep TCP connection ESTABLISHED. Rather the connection go to
        CLOSE_WAIT and raise errors CannotSendRequest or the server reply with
        empty and it raise BadStatusLine
        """
        self.__conn = HTTPSConnection(self.API_HOSTANME) # reload
        self.__conn.timeout = 10

    def __conn_request(self, http_verb, endpoint, params):
        """
        Wrapper to request/response of httplib's context, reload a
        connection if presume that error will occurs and returns the response
        """
        try:
            self.__conn.request(http_verb, endpoint, params, self.headers)
        except CannotSendRequest:
            self.__reload_conn()
            self.__conn.request(http_verb, endpoint, params, self.headers)

        try:
            response = self.__conn.getresponse()
        except (IOError, BadStatusLine):
            self.__reload_conn()
            self.__conn.request(http_verb, endpoint, params, self.headers)
            response = self.__conn.getresponse()

        return response

    def get_with_api_token(self, endpoint, fields):
        """ Make request when require provide API ACCESS TOKEN that can
        be API|SECRET. Returns a python's dictionary.
        """
        fields.append(("access_token", self.ACCESS_TOKEN))
        params = urlencode(fields, True)
        endpoint = ''.join([endpoint, params])
        response = self.__conn_request("GET", endpoint, None)
        return self.__validation(response)

    def get(self, endpoint, fields):
        params = urlencode(fields, True)
        endpoint = ''.join([endpoint, params])
        response = self.__conn_request("GET", endpoint, None)
        return self.__validation(response)

    def debug_token(self, input_token):
        """ Make request to /debug_token? endpoint. This returns info on
        accessToken provided by user after Login Box via JS SDK.

        :param input_token: is accessToken provided by user
        """
        endpoint = "/debug_token?"
        fields = [('input_token', input_token)]
        return self.get_with_api_token(endpoint, fields)

    def check_app_id(self, input_token):
        """ Make validation and returns TRUE if app_id in response
        from debug_token is valid.

        :param input_token: is accessToken provided by user
        """
        if not input_token:
            input_token = self.user_access_token

        debug_response = self.debug_token(input_token)

        if self.APP_ID == debug_response['data']['app_id']:
            return True

        return False

    def get_user_public_info(self, input_token):
        """ Gets public info from facebook API

        :param input_token: accessToken provides by FB SDK (js)
        """

        endpoint = "/me?"
        fields = [("access_token", input_token)]
        response = self.get(endpoint, fields)
        return response
