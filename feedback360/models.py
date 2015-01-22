# -*- coding: UTF-8 -*-

from mongoengine import *
from mongoengine.fields import EmailField, BooleanField
from mongoengine.base import BaseList
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


CHOICES_LEVEL_PROXIMITY = (
    (0, 'more 5 times'), # per week
    (1, 'one or twice per month'),
    (2, 'sporadically'),
    (9, 'interested'),
)


class Invite(Document):
    """ Invite that request a person by admin role. This moment we not have
    the emails but only social name (first_name and last_name).

    :field social_name: is social name from social network, but sanitized or
    lowercase.
    :field display_name: is original display name in social network. It isn't
    allow modifications.
    """
    social_name = StringField(max_length=100, required=True, primary_key=True)
    display_name = StringField(max_length=100, required=False)
    social_username = StringField(max_length=80, required=False, default=None)
    email = EmailField(verbose_name=_('e-mail address'), required=False,
                       unique=False)
    proximity = IntField(choices=CHOICES_LEVEL_PROXIMITY, required=True)
    interested = BooleanField(default=False) # not invited, but have interest

    def __unicode__(self):
        return self.display_name, self.proximity

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

    @classmethod
    def was_invited(cls, name):
        """ Verify if name was invited or is only interested

        :param name: social name. It' not username
        :return: Obj or False if DoesNotExist (or not matching w/ criteria).
        """

        try:
            obj = Invite.objects.get(social_name=name.lower(), interested=False)
        except DoesNotExist:
            return False

        return obj

    @classmethod
    def set_interested(cls, name, email):
        """ Makes one person interested and gets data from social plugins.
        (here) We have email address after social login. You before can call
        is_interested (see it).

        :param name: social name captured by plugin social
        :param email: email captured by plugin social
        """

        # This approach allow to left dynamic the option "others" of the
        # CHOICES_LEVEL_PROXIMITY
        proximity = CHOICES_LEVEL_PROXIMITY[-1][0]

        # lower
        name = name.lower()

        if not cls.is_interested(name=name):
            invite = Invite(social_name=name, email=email, proximity=proximity,
                        interested=True)
            invite.save()

    @classmethod
    def is_interested(cls, name=None, email=None):
        """ Verify if name has interest.

        :param name: social name. It' not username
        :para email: due email to be insert by set_interested, we have email
        :return: boolean
        """

        if name:
            name = name.lower()

        try:
            if email:
                obj = Invite.objects.get(email=email, interested=True)
            else:
                obj = Invite.objects.get(social_name=name, interested=True)
        except DoesNotExist:
                return False
        except:
          raise

        return True

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.social_name
        self.social_name = self.social_name.lower()
        super(Invite, self).save(*args, **kwargs)


class Participant(Document):
    """ The person did invited

    TODO: to incorporate this class in Invite class
	"""
    name = StringField(max_length=100, required=True)
    email = EmailField(verbose_name=_('e-mail address'), primary_key=True)
    sent_replies = BooleanField(default=False)
    proximity = IntField()

    def __unicode__(self):
        return "{name}:{proximity}".format(name=self.name,
                                           proximity=self.proximity)

    @classmethod
    def is_participant(cls, social_name):
        try:
            participant = Participant.objects.get(name=social_name.lower())
        except DoesNotExist:
            return False

        return participant

    @property
    def was_sent(self):
        """ Confirms if participant sent replies
        :return: Boolean True if sent
        """
        return self.sent_replies

    def get_enunciation(self):
        """ To use this to reveal the enunciation's to participants. This
        to filter the questions that him can reply.
        """
        return Asks.objects(proximity__gte=self.proximity)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        if Invite.was_invited(self.name.lower()):
            return super(Participant, self).save(*args, **kwargs)
        else:
            raise TypeError("Invitation is required.")

class Asks(Document):
    """ Class admin of Asks
    """
    TYPE_REPLY = (
        (0, 'essay'),
        (1, 'simple matching'),
        (2, 'multiple-choice'),
    )
    # the important thing is that the questions reflect your learning objectives
    # Write instructions that are clear, explicit, and unambiguous.
    # Avoid complex and convoluted sentence constructions, double negatives,
    # and idiomatic language that may be difficult for students, especially
    # international students, to understand
    # multiple-choices - to test illogical concepts is good
    # Test only a single idea in each item.
    enunciation = StringField(max_length=255, required=True)
    proximity = IntField(choices=CHOICES_LEVEL_PROXIMITY, default=2)
    reply_type = IntField(choices=TYPE_REPLY, default=0)
    reply_accepted = ListField(StringField(max_length=255, required=False))

    def __unicode__(self):
        return self.enunciation

    def get_verbose_choices(self):
        return dict(CHOICES_LEVEL_PROXIMITY)[self.proximity]

    def get_verbose_type_reply(self):
        return dict(self.TYPE_REPLY)[self.reply_type]

    def _sanitize_reply_accepted(self):
        """ Checks and fix string in field for change it to list type.
        """
        if self.reply_type == 1 or self.reply_type == 2:
            if isinstance(self.reply_accepted, str):
                self.reply_accepted = self.reply_accepted.split(';')
                return self.reply_accepted

        if self.reply_type == 0:
            self.reply_accepted = [str(self.reply_accepted)]

    def save(self, *args, **kwargs):
        self._sanitize_reply_accepted()
        super(Asks, self).save(*args, **kwargs)


class Replies(Document):
    proximity = IntField(choices=CHOICES_LEVEL_PROXIMITY)
    reply = StringField(max_length=255)
    ask = ReferenceField(Asks)

    def __unicode__(self):
        return self.reply

class MarketFit(Document):
    name = StringField(max_length=120)
    email = EmailField()
    personal_use = BooleanField(default=False)
    company_use = BooleanField(default=False)
    company_name = StringField(max_length=120)
