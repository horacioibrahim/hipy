#coding: utf-8

from mongoengine import *
from mongoengine.fields import EmailField, BooleanField
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


CHOICES_LEVEL_PROXIMITY = (
    (0, 'more 5 times'), # per week
    (1, 'one or twice per month'),
    (3, 'sporadically'),
    (4, 'interested'),
)


class Invite(Document):
    """ Invite that request a person by admin role. This moment we not have
    the emails but only social name (first_name and last_name)
    """
    social_name = StringField(max_length=100, required=True, primary_key=True,
                              unique=True)
    social_username = StringField(max_length=80, required=False, default=None)
    email = EmailField(verbose_name=_('e-mail address'), required=False,
                       unique=True) # support more queries
    proximity = IntField(choices=CHOICES_LEVEL_PROXIMITY, required=True)
    interested = BooleanField(default=False) # not invited, but have interest

    def __split_social_name(self):
        return self.social_name.split()

    def __default_email(self):
        """ Useful to solve default value to email field. This because if the
        value be repeated a problem (in MongoDB level) is raised.
        """
        email_default = lambda n, s: "{name}{surname}@{name}.{surname}".format(
                        name=n, surname=s)
        name, surname = self.__split_social_name()
        if not self.email:
            return email_default(name, surname)

        # This was passed by user
        return self.email


    @staticmethod
    def was_invited(name):
        """ Verify if name was invited or is only interested

        :param name: social name. It' not username
        :return: boolean
        """

        try:
            obj = Invite.objects.get(social_name=name, interested=False)
        except:
            obj = None

        if obj:
            return True

        return False

    @staticmethod
    def set_interested(name, email):
        """ Makes one person interested and gets data from social plugins.
        (here) We have email address after social login.

        :param name: social name captured by plugin social
        :param email: email captured by plugin social
        """
        proximity = 4
        invite = Invite(social_name=name, email=email, proximity=proximity,
                        interested=True)
        invite.save()
        return invite

    def is_interested(self, name=None, email=None):
        """ Verify if name has interest.

        :param name: social name. It' not username
        :para email: due email to be insert by set_interested, we have email
        :return: boolean
        """
        check_data = self.social_name if self.social_name else name
        email = self.email if self.email else email

        try:
            if email:
                obj = Invite.objects.get(email=email, interested=True)
            else:
                obj = Invite.objects.get(social_name=check_data, interested=True)
        except:
            obj = None

        if obj:
            return True

        return False

    def save(self, *args, **kwargs):
        self.email = self.__default_email()
        super(Invite, self).save(*args, **kwargs)


class Participant(Document):
    """ The person did invited
	"""
    name = StringField(max_length=100, required=False)
    email = EmailField(verbose_name=_('e-mail address'), primary_key=True)
    sent_replies = BooleanField(default=False)
    proximity = IntField()

    def has_invitation(self, email):
        """ Checks if a person has invitation or exists in Invite scope.
        :param email:
        :return:
        """
        try:
            self.invite = Invite.objects.get(email=email)
        except DoesNotExist:
            return False

        self.proximity = self.invite.proximity

        return self.invite.was_invited(self.invite.social_name)

    @property
    def was_sent(self):
        """ Confirms if participant sent replies
        :return: Boolean True if sent
        """
        return self.sent_replies

    def save(self, *args, **kwargs):
        # checks if the person have invitation
        if self.has_invitation(self.email):
            super(Participant, self).save(*args, **kwargs)
        else:
            raise TypeError("The person with name and email wasn't invited")

        return self


class Asks(Document):
    """ Class admin of Asks
    """
    enunciation = StringField(max_length=120, required=True)


class Replies(Document):
    proximity = IntField(choices=CHOICES_LEVEL_PROXIMITY)
    reply = StringField(max_length=255)
    ask = ReferenceField(Asks)










