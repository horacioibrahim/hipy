# -*- coding: UTF-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from mongoengine import DoesNotExist, NotUniqueError

#app
from . import models, forms
from main.utils import FacebookAPIRequests

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
            access_token = form.cleaned_data['access_token']
            fb = FacebookAPIRequests()
            user_profile = fb.get_user_public_info(access_token)
            name = user_profile['name']
            email = user_profile['email']
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

                return replies(request, name)

            else:

                # turn on an interested
                models.Invite.set_interested(name, email)
                # redirect thanks for interested
                return thanks_for_interest(request)

    return redirect(reverse('feedback360_home'))

def replies(request, social_name=None):
    form = None
    empty = None
    Participant = models.Participant

    if not social_name:
        social_name = request.POST.get('social_name', None)
        if social_name is None:
            raise Http404(_('User or invitation does not exist.'))

    participant = Participant.is_participant(social_name)
    asks_permitted = participant.get_enunciation()
    asks_ids_permitted = [str(ask.pk) for ask in asks_permitted]

    if not participant:
        return redirect(reverse('feedback360_home'))

    if request.path_info == reverse('replies'):
        if request.method == "POST":
            replies_fields =  dict(request.POST.iterlists())
            replies_for_bulk = []

            for fieldname, values in replies_fields.items():
                # This moment the field social_name submitted in form
                # already used to get the participant.
                if fieldname.startswith('reply_'):
                    askid = fieldname.split('_')[1]

                    if askid not in asks_ids_permitted:
                        raise TypeError("This question is not "
                                            "applicable for you.")

                    # Receives askid, proximity and reply for each reply
                    # but the form submit reply_askid, social_name.
                    doc = models.Replies(**{'ask': askid,
                                    'proximity': participant.proximity,
                                                        'reply': values})
                    replies_for_bulk.append(doc)

            resp = models.Replies.objects.insert(replies_for_bulk)
            participant.sent_replies = True
            participant.save()
            return thanks_for_replies(request)

        else:
            form = forms.RepliesForm()


    return render(request, 'feedback360/replies.html',
                  dict(form=form, participant=participant, empty=empty))

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
                ask.reply_type = form.cleaned_data['reply_type']
                ask.reply_accepted = form.cleaned_data['reply_accepted']
                ask.save()
                # form.save()
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
