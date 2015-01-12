__author__ = 'horacioibrahim'

from django import forms
from mongodbforms import DocumentForm, CharField, IntegerField

# app
from . import models

class InviteForm(DocumentForm):

    class Meta:
        model = models.Invite
        fields = ['social_name', 'proximity']


class AccessControlForm(forms.Form):
    social_name = forms.CharField(max_length=100)
    email = forms.EmailField()


class InviteDelForm(forms.Form):
    social_name = forms.CharField(max_length=100)
    proximity = forms.IntegerField(required=False)


class AsksForm(DocumentForm):
    enunciation = CharField(widget=forms.Textarea)
    proximity = IntegerField(initial=2,
            label="Proximity: (usage: 0 - more 5 times, \
            1 - one or twice per month, 2 - sporadically [default])")

    class Meta:
        model = models.Asks
        fields = ['enunciation', 'proximity']


class RepliesForm(DocumentForm):
    reply = CharField(widget=forms.Textarea)

    class Meta:
        model = models.Replies
        fields = ['reply']



