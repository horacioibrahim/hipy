# -*- coding: UTF-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from mongoengine import DoesNotExist, NotUniqueError

#app
from . import models, forms

def home(request):
    return render(request, 'feedback360/home.html')

def access_control(request):
    """ This is like the control youtube video unlisted. Who
    have the link will can to reply. The difference is the "links"
    are joined-up from name and email.
    """
    name = None
    email = None
    invitation = None

    if request.method == "POST":
        form = forms.AccessControlForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['social_name']
            email = form.cleaned_data['email']
            invitation = models.Invite.was_invited(name)

            if invitation:
                try:
                    is_participant = models.Participant.objects.get(
                            name=invitation.social_name,
                            proximity=invitation.proximity)
                except DoesNotExist:
                    is_participant = False

                if is_participant and is_participant.sent_replies:
                    return redirect(reverse('thanks_replies'))

                if not is_participant:
                    # turn on as participant
                    participant = models.Participant()
                    participant.name = invitation.social_name
                    participant.email = email
                    participant.proximity = invitation.proximity
                    participant.save()

                return redirect(reverse('replies'))
            else:

                # turn on an interested
                models.Invite.set_interested(name, email)
                # redirect thanks for interested
                return thanks_for_interest(request)

    return redirect(reverse('feedback360_home'))

def replies(request):
    form = None
    Participant = models.Participant

    if Participant.is_participant('test'):
        pass

    if request.method == "POST":
        form = forms.RepliesForm(request.POST)
        if form.is_valid():
            form.save()

    else:
        form = forms.RepliesForm()


    return render(request, 'feedback360/replies.html', dict(form=form))

def thanks_for_interest(request):
    return render(request, 'feedback360/thanks_for_interest.html')

def thanks_for_replies(request):
    return render(request, 'feedback360/thanks_for_replies.html')

def remove_from_facebook(request):
    return render(request, 'feedback360/remove.html')

@login_required
def add_invite(request):
    form = None

    if request.method == 'POST':
        if request.user.is_superuser:
            form = forms.InviteForm(request.POST)
            if form.is_valid():
                proximity = form.cleaned_data['proximity']
                social_name = form.cleaned_data['social_name']

                invite = models.Invite(social_name=social_name,
                                       proximity=proximity)
                try:
                    invite.save()
                except NotUniqueError:
                    social_name = social_name.lower()
                    invite = models.Invite.objects.get(social_name=social_name)
                    invite.proximity = proximity
                    invite.save()

                # invite = form.save() # Error with repeated id's
                # print invite.pk
                if request.is_ajax():
                    return HttpResponse(invite.to_json(),
                                        content_type="application/json")
            else:
                # form can invalid due existent register (document)
                # for theses cases follow below an workaround:
                social_name = request.POST.get('social_name', None)
                proximity = request.POST.get('proximity', None)
                if social_name and proximity:
                    try:
                        invite = models.Invite.objects.get(
                            social_name=social_name.lower(), interested=False)
                        invite.proximity = int(proximity)
                        invite.save()
                    except DoesNotExist:
                        pass
                # end workaround for message of invalid by existent data
                raise TypeError(form._errors) # DEBUG PURPOSE

    else:
        form = forms.InviteForm()

    return render(request, 'feedback360/add_invite.html', dict(form=form))

@login_required
def del_invite(request):
    form = None

    if request.method == 'POST':
        if request.user.is_superuser:
            form = forms.InviteDelForm(request.POST)
            if form.is_valid():
                social_name = request.POST.get('social_name', None)
                proximity = request.POST.get('proximity', None)
                try:
                    invite = models.Invite.objects.get(
                                    social_name=social_name.lower())
                    invite.delete()
                except DoesNotExist:
                    pass
    else:
        form = forms.InviteForm()

    return render(request, 'feedback360/del_invite.html', dict(form=form))

@login_required
def add_ask(request):
    form = None

    if request.method == 'POST':
        if request.user.is_superuser:
            form = forms.AsksForm(request.POST)
            if form.is_valid():
                ask = models.Asks()
                ask.enunciation = form.cleaned_data['enunciation']
                ask.proximity = form.cleaned_data['proximity']
                ask.save()
                # form.save()
            else:
                raise TypeError('opopopopo')
    else:
        form = forms.AsksForm()

    asks = models.Asks.objects()
    return render(request, 'feedback360/add_asks.html',
                                        dict(form=form, asks=asks))

@login_required
def del_ask(request, pk):

    if request.user.is_superuser:

        try:
            ask = models.Asks.objects.get(pk=pk)
            ask.delete()
        except:
            pass # not exists

    return redirect(reverse('add_ask'))

def list_participants(request):
    pass

def list_replies(request, by_ask=None):
    pass