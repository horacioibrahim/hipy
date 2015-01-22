# -*- coding: UTF-8 -*-
__author__ = 'horacioibrahim'

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from mongodbforms import DocumentForm, CharField, IntegerField

# app
from . import models

class InviteForm(DocumentForm):

    class Meta:
        model = models.Invite
        fields = ['social_name', 'proximity']


class AccessControlForm(forms.Form):
    access_token = forms.CharField(max_length=255)


class InviteDelForm(forms.Form):
    social_name = forms.CharField(max_length=100)
    proximity = forms.IntegerField(required=False)


class AsksForm(DocumentForm):
    enunciation = CharField(widget=forms.Textarea)
    proximity = IntegerField(initial=2,
            label="Proximity: (usage: 0 - more 5 times, \
            1 - one or twice per month, 2 - sporadically [default])")

    reply_accepted = CharField(required=False,
                        label=_("For Single Matching or Multiple choice: "
                        "choices separated by semiolon (;)."))

    class Meta:
        model = models.Asks
        fields = ['enunciation', 'proximity', 'reply_type', 'reply_accepted']

    def clean_reply_accepted(self):
        data = self.cleaned_data['reply_accepted']
        data_reply_type = self.cleaned_data['reply_type']
        is_blanks = data.replace(" ", "")

        if len(is_blanks) == 0 and (data_reply_type == 1 or data_reply_type == 2):
            raise ValidationError(_('reply_type field require accepted replies.'))

        if data_reply_type == 0 and len(is_blanks) > 0:
            raise ValidationError(_("Type's Ask cannot receive replies."))

        data = data.split(';')

        return data


class RepliesForm(forms.Form):
    wrapform = forms.CharField(max_length=120)


class MarketFit(DocumentForm):
    personal_use = forms.BooleanField(required=False,
    label='Marque se gostaria de ter uma avaliação 360º')
    company_use = forms.BooleanField(required=False,
    label='Marque se acredita que pode ser útil para sua Empresa')
    company_name = forms.CharField(required=False,
        label='Se respondeu a questão anterior informe o nome da sua Empresa')
    email = forms.CharField(required=True,
        label='Se respondeu a questão anterior informe o seu e-mail')
    name = forms.CharField(required=False,
        label='Seu nome para contato')

    class Meta:
        model = models.MarketFit
        fields = ['personal_use', 'company_use', 'company_name', 'email',
                    'name']
