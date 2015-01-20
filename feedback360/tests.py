# -*- coding: utf-8 -*-

import os
from django.test import Client, RequestFactory, SimpleTestCase
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from mongoengine.queryset import DoesNotExist
from bson import ObjectId

# APP
from blog import models as blog_models
from . import models, views, forms
from main.utils import relative_path_url, FacebookAPIRequests


PROXIMITY =  models.CHOICES_LEVEL_PROXIMITY[-1][0] # more dynamic

class TestFeedback360(SimpleTestCase):
    def setUp(self):
        email = 'user_silva@gmail.com'
        social_name = 'User Silva'
        proximity = 0
        i = models.Invite()
        i.email = email
        i.social_name = social_name
        i.proximity = proximity
        i.save()
        self.invite = i

    def tearDown(self):
        self.invite.delete()

    def test_invited_was_invited(self):
        name = 'Horacio Ibrahim'
        check_invite = models.Invite.was_invited(self.invite.social_name)
        self.assertTrue(check_invite)
        # not invited
        check_not_invited = models.Invite.was_invited('Not Invited')
        self.assertFalse(check_not_invited)

    def test_invited_set_interested(self):
        models.Invite.set_interested('Mario Lago',
                                                'mlago@gmail.com')
        obj = models.Invite.objects.get(social_name='Mario Lago'.lower(),
                                        interested=True)
        self.assertIsInstance(obj, models.Invite)
        self.assertEqual(obj.social_name, 'Mario Lago'.lower())

    def test_invited_is_interested(self):
        def make_interested():
            models.Invite.set_interested(name='Joao Batista', email='jb@j.co')
        make_interested()
        check_interest = models.Invite().is_interested(name='Joao Batista')
        self.assertTrue(check_interest)
        check_interest = models.Invite().is_interested(email='jb@j.co')
        self.assertTrue(check_interest)
        check_interest = models.Invite().is_interested(email='pocoyo@pc.com')
        self.assertFalse(check_interest)

    def test_participant_save(self):
        email = self.invite.email
        social_name = self.invite.social_name
        participant = models.Participant(name=social_name, email=email)
        obj = participant.save()
        self.assertIsInstance(obj, models.Participant)

    def test_participant_create_not_invited(self):
        name='Anna Lelis'
        email='annale@m.co'
        participant = models.Participant(name=name, email=email)
        self.assertRaises(TypeError, participant.save)

    def test_participant_was_sent(self):
        # Checks if participant already sent replies.
        participant = models.Participant(name=self.invite.social_name,
                           email=self.invite.email)
        obj = participant.save()
        self.assertFalse(obj.was_sent)
        obj.sent_replies = True
        obj.save()
        new_participant = models.Participant.objects.get(email=self.invite.email)
        self.assertTrue(new_participant.was_sent)

    def test_asks_reply_accepted_reply_type_0_error(self):
        # test if data semicolon separated is valid
        ask = models.Asks()
        ask.enunciation = "A simple test"
        ask.reply_type = 0
        ask.reply_accepted = "Yes; No; Maybe"
        ask.save()
        ask_obj = models.Asks.objects.get(pk=ask.pk)
        self.assertEqual("Yes; No; Maybe", ask_obj.reply_accepted[0])

    def test_asks_reply_accepted_reply_type_0(self):
        # test if data semicolon separated is valid
        ask = models.Asks()
        ask.enunciation = "A simple test"
        ask.reply_type = 0
        # if reply_type is 0 not provides reply_accepted
        # ask.reply_accepted = "Yes; No; Maybe"
        ask.save()
        self.assertEqual(len(ask.reply_accepted), 1)
        self.assertEqual(ask.reply_accepted[0], '[]')

    def test_asks_reply_accepted_reply_type_1(self):
        # test if data semicolon separated is valid
        ask = models.Asks()
        ask.enunciation = "A simple test"
        ask.reply_type = 1
        ask.reply_accepted = "Yes; No; Maybe"
        ask.save()
        self.assertIsInstance(ask.reply_accepted, list)
        self.assertEqual(len(ask.reply_accepted), 3)

    def test_asks_reply_accepted_reply_type_2(self):
        # test if data semicolon separated is valid
        ask = models.Asks()
        ask.enunciation = "A simple test"
        ask.reply_type = 2
        ask.reply_accepted = "Yes; No; Maybe"
        ask.save()
        self.assertIsInstance(ask.reply_accepted, list)
        self.assertEqual(len(ask.reply_accepted), 3)


class TestClientTestFeedback360(SimpleTestCase):
    """
        Tests that behaves like user in browser.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.c = Client()
        # user accessToken from Login box
        self.token = os.environ.get('TEMPTOKEN')
        fb = FacebookAPIRequests()
        user_public_info = fb.get_user_public_info(self.token)
        self.name = user_public_info['name']
        self.email = user_public_info['email']

        # get or create superuser
        try:
            self.superuser = blog_models.User.objects.get(username='tester')
        except DoesNotExist:
            self.superuser = blog_models.User.create_user(
                username='tester', password='123', email='tester@tester.co')
            self.superuser.is_superuser = True
            self.superuser.is_staff = True
            self.superuser.save()

        # get or create ordinary user
        try:
            self.user = blog_models.User.objects.get(username='tester')
        except DoesNotExist:
            # create superuser
            self.user = blog_models.User.create_user(username='tester',
                            password='123', email='tester@tester.co')

        def clean_asks():
            asks = models.Asks.objects()
            for ask in asks:
                ask.delete()
        self.clean_asks = clean_asks

    def test_home(self):
        # Create an instance of a GET request
        request = self.factory.get('/feedback360/home')

        # Anonymous user
        # request.user = AnonymousUser()

        # test the view
        response = views.home(request)
        self.assertEqual(response.status_code, 200)

    def test_access_control(self):
        # test if open thanks template...
        response = self.c.post("/feedback360/access/",
                    data={'access_token': self.token})

        template_name = response.templates[0].name
        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_name, 'feedback360/thanks_for_interest.html')

    def test_access_control_invited(self):
        # test if access control to invited
        social_name = self.name
        email = self.email
        proximity = 2
        # change invite ... created in previous test_
        invite = models.Invite.objects.get(social_name=social_name.lower())
        invite.interested = False
        invite.save() # invitation created
        #
        response = self.c.post("/feedback360/access/",
                                data={'access_token': self.token})
        template_name = response.templates[0].name
        self.assertEqual(template_name, 'feedback360/replies.html')
        self.assertEqual(200, response.status_code)

    def test_access_control_invited_participant_replies_False(self):
        social_name = self.name
        email = self.email
        response = self.c.post("/feedback360/access/",
                    data={'access_token': self.token})

        participant = models.Participant.objects.get(email=email)
        self.assertIsInstance(participant, models.Participant)
        template_name = response.templates[0].name
        self.assertEqual(template_name, 'feedback360/replies.html')
        self.assertEqual(200, response.status_code)

    def test_access_control_invited_participant_replies_True(self):
        social_name = self.name
        email = self.email
        participant = models.Participant.objects.get(email=email)
        participant.sent_replies = True
        participant.save()
        response = self.c.post("/feedback360/access/",
                                data={'access_token': self.token})

        relative_path = relative_path_url(response.url)
        participant = models.Participant.objects.get(email=email)
        self.assertEqual('/feedback360/replies/thanks/', relative_path)
        self.assertIsInstance(participant, models.Participant)
        self.assertEqual(response.status_code, 302)

    def test_add_invite(self):
        social_name = 'XZY ABCZ'
        request = self.factory.post('/feedback360/invitation/add',
                        data={'social_name': social_name,
                                        'proximity': PROXIMITY})

        request.user = self.superuser
        response = views.add_invite(request)
        self.assertEqual(response.status_code, 200)
        invite = models.Invite.objects.get(social_name=social_name.lower())
        self.assertEqual(social_name.lower(), invite.social_name)

    def test_add_invites(self):
        iv = models.Invite.objects()
        for i in iv:
            i.delete()
        # One
        social_name = 'XZY One'
        request = self.factory.post('/feedback360/invitation/add',
                        data={'social_name': social_name,
                                        'proximity': 1})
        request.user = self.superuser
        response = views.add_invite(request)
        self.assertEqual(response.status_code, 200)
        # Two
        social_name = 'XZY Two'
        request = self.factory.post('/feedback360/invitation/add',
                        data={'social_name': social_name,
                                        'proximity': 2})
        request.user = self.superuser
        response = views.add_invite(request)
        self.assertEqual(response.status_code, 200)
        iv = models.Invite.objects()
        self.assertEqual(2, len(iv))

    def test_add_invite_edit_existent(self):
        # test if proximity is changed for an existent register
        social_name = 'XZY ABCZ'
        request = self.factory.post('/feedback360/invitation/add',
                        data={'social_name': social_name,
                                        'proximity': 1})

        request.user = self.superuser
        response = views.add_invite(request)
        invite = models.Invite.objects.get(social_name=social_name.lower())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(social_name.lower(), invite.social_name)
        self.assertEqual(1, invite.proximity)

    def test_del_invite(self):
        # add manually
        iv = models.Invite(social_name='More Travel', proximity=0)
        iv.save()
        social_name = 'XZY ABCZ'
        request = self.factory.post('/feedback360/invitation/del',
                        data={'social_name': 'More Travel',
                              'proximity': 0})

        request.user = self.superuser
        response = views.del_invite(request)
        invite = models.Invite.objects.get
        self.assertEqual(response.status_code, 200)
        self.assertRaises(DoesNotExist, invite, social_name=social_name)

    def test_add_invite_second(self):
        social_name = 'ABC DEFG'
        request = self.factory.post('/feedback360/invitation/add',
                        data={'social_name': social_name,
                                        'proximity': PROXIMITY})

        request.user = self.superuser
        response = views.add_invite(request)
        invite = models.Invite.objects.get(social_name=social_name.lower())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(social_name.lower(), invite.social_name)

    def test_add_ask(self):
        asks = models.Asks.objects()
        for ask in asks:
            ask.delete()

        request = self.factory.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics',
                          'proximity': 2,
                          'reply_type': 0,
                          'reply_accepted': ''})
        request.user = self.superuser
        response = views.add_ask(request)
        asks = models.Asks.objects()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(asks))

    def test_add_ask_2(self):
        request = self.factory.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics two',
                          'proximity': 1})
        request.user = self.superuser
        response = views.add_ask(request)
        asks = models.Asks.objects()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(asks))

    def test_del_ask(self):
        ask = models.Asks()
        ask.enunciation = "What is your name"
        ask.proximity = 0
        ask.save()
        url_delete = "/feedback360/asks/del/{}".format(ask.pk)
        request = self.factory.get(url_delete)
        request.user = self.superuser
        response = views.del_ask(request, ask.pk)
        ask_get = models.Asks.objects.get
        self.assertEqual(response.status_code, 302)
        self.assertRaises(DoesNotExist, ask_get, pk=ask.pk)

    def test_participant_get_enunciation(self):
        # Test the enunciation's available to participant
        # Deleting existent asks
        all_asks = models.Asks.objects()
        for ak in all_asks:
            ak.delete()
        # Add ask
        ask = models.Asks()
        ask.enunciation = "What is your name?"
        ask.proximity = 2
        ask.save()
        # --
        ask = models.Asks()
        ask.enunciation = "How do you do?"
        ask.proximity = 0
        ask.save()
        # Invite is required to be participant
        # Add invite
        invite = models.Invite()
        invite.social_name = "Augusto Cury"
        invite.proximity = 1
        invite.save()
        # Add participant
        participant = models.Participant()
        participant.name = "Augusto Cury"
        participant.proximity = 1
        participant.email = "acury@cury.co"
        participant.save()
        self.assertEqual(1, len(participant.get_enunciation()))
        participant.proximity = 0
        self.assertEqual(2, len(participant.get_enunciation()))

    def test_add_ask_with_reply_type_1(self):

        self.clean_asks()
        request = self.factory.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics',
                          'proximity': 2,
                          'reply_type': 1,
                          'reply_accepted': 'yes; no; maybe'
                          })
        request.user = self.superuser
        response = views.add_ask(request)
        asks = models.Asks.objects()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(asks))
        self.assertEqual(3, len(asks[0].reply_accepted))

    def test_add_ask_with_reply_type_2(self):
        self.clean_asks()
        request = self.factory.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics',
                          'proximity': 2,
                          'reply_type': 2,
                          'reply_accepted': 'yes; no; maybe'
                          })
        request.user = self.superuser
        response = views.add_ask(request)
        asks = models.Asks.objects()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(asks))
        self.assertEqual(3, len(asks[0].reply_accepted))

    def test_add_ask_with_reply_type_0(self):
        self.clean_asks()
        request = self.factory.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics',
                          'proximity': 2,
                          'reply_type': 0,
                          'reply_accepted': ''
                          })
        request.user = self.superuser
        response = views.add_ask(request)
        asks = models.Asks.objects()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(asks))
        self.assertEqual(1, len(asks[0].reply_accepted))

    def test_add_ask_with_reply_type_0_except(self):
        self.clean_asks()
        self.c.login(username=self.superuser.username, password="123")
        response = self.c.post("/feedback360/asks/add/",
                    data={'enunciation': 'characteristics',
                          'proximity': 2,
                          'reply_type': 0,
                          'reply_accepted': 'yes; no; maybe'
                          })
        self.assertContains(response, 'Type&#39;s Ask cannot receive replies.',
            count=None, status_code=200, msg_prefix='', html=False)


class TestReplies(SimpleTestCase):

    def setUp(self):
        def clean_asks():
            asks = models.Asks.objects()
            for ask in asks:
                ask.delete()
        self.clean_asks = clean_asks

        def reply_field(askid):
            return 'reply_%s' % askid

        self.rf = reply_field
        self.c = Client()
        invites = (('Steve Jobs', 0, 'st@jobs.co'),
                   ('Ayrton Senna', 0, 'as@as.co'),
                   ('Flavio Augusto', 1, 'fa@fa.co'),
                   ('Ana Thomaz', 1, 'at@at.co'),
                    ('Murilo Gun', 2, 'mg@mg.co'),
                    ('Steve Woz', 2, 'sw@sw.co'))
        asks = (
                ('Why to build projects?', 2),
                ('How him sees the world?', 0),
                ('Are you worked with him?', 1),
        )
        self.invites = invites
        # creates invites for each proximity
        for social_name, proximity, email in invites:
            invite = models.Invite(social_name=social_name,
                                                proximity=proximity)
            invite.save()
            # creates participant
            p = models.Participant(name=social_name,
                                   proximity=proximity, email=email)
            p.save()

        # creates asks with filters for each proximity
        self.asks_ids = []
        for enunciation, proximity in asks:
            ask = models.Asks(enunciation=enunciation,
                proximity=proximity, reply_accepted='')
            ask.save()
            self.asks_ids.append(ask.pk)

    def tearDown(self):
        invites = models.Invite.objects()
        participants = models.Participant.objects()
        asks = models.Asks.objects()
        for iv in invites:
            iv.delete()
        for ask in asks:
            ask.delete()
        for participant in participants:
            participant.delete()

    def test_replies_empty(self):
        # test post without replies
        askid = self.asks_ids[0]
        reply_field = 'reply_%s' % askid
        response = self.c.post('/feedback360/replies/', data={reply_field: '',
                            'social_name': 'Steve Jobs'})

        error_message = response.context['messages']
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(error_message, FallbackStorage) # TODO: if error

    def test_replies_once(self):
        # test post with once reply
        social_name = self.invites[0][0]
        proximity = self.invites[0][1]
        # SETUP to local
        # clean replies
        replies = models.Replies.objects()
        for reply in replies:
            reply.delete()
        # POST
        response = self.c.post('/feedback360/replies/',
            data={
            'reply_%s' % self.asks_ids[0]: 'Yeah, good and useful projects.',
            'social_name': social_name})
        replies = models.Replies.objects()
        participant = models.Participant.is_participant(social_name)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(replies))
        self.assertEqual(self.asks_ids[0], ObjectId(replies[0].ask.id))
        self.assertEqual(proximity, replies[0].proximity)
        self.assertTrue(participant.sent_replies)
        self.assertEqual(response.templates[0].name,
                                'feedback360/thanks_for_replies.html')

    def test_replies_not_permitted(self):
        # Test if ask with filtered proximity
        # SETUP local
        # clean replies
        replies = models.Replies.objects()
        for reply in replies:
            reply.delete()
        # get user with proximty 2
        for name, proximity, email in self.invites:
            if proximity == 2:
                break
        # POST
        #response = self.c.post()
        reply_field_0 = self.rf(self.asks_ids[0])
        reply_field_1 = self.rf(self.asks_ids[1])
        reply_field_2 = self.rf(self.asks_ids[2])
        self.assertRaises(TypeError, self.c.post,'/feedback360/replies/',
                            data={
                            reply_field_0: ['One reply'],
                            reply_field_1: ['Two reply'],
                            reply_field_2: ['Three reply'],
                            'social_name': [name, name, name]})

    def test_replies_permitted(self):
        # Test replies to all asks permitted
        # SETUP local
        # clean replies
        replies = models.Replies.objects()
        for reply in replies:
            reply.delete()
        # get user with proximty 2
        for name, proximity, email in self.invites:
            if proximity == 2:
                break
        # get asks permitted
        asks = models.Asks.objects(proximity=proximity)
        social_name_list_replies = []
        data = {}
        for counter, ask in enumerate(asks):
            reply_field = self.rf(str(ask.pk))
            data[reply_field] = "My reply %s " % counter
            social_name_list_replies.append(name)

        data['social_name'] = social_name_list_replies

        # POST
        response = self.c.post('/feedback360/replies/',
                            data=data)
        replies = models.Replies.objects()
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(asks), len(replies))

    def test_replies_with_reply_type(self):
        # Clean database target collections
        self.clean_asks()
        replies = models.Replies.objects()
        for r in replies:
            r.delete()

        _asks = [
            {
                'enunciation': 'Essay replies',
                'proximity': 2,
                'reply_type': 0,
                'reply_accepted': ''
            },
            {
                'enunciation': 'Single matching replies',
                'proximity': 2,
                'reply_type': 1,
                'reply_accepted': 'yes; no; maybe'
            },
            {
                'enunciation': 'Multiple-choice replies',
                'proximity': 2,
                'reply_type': 2,
                'reply_accepted': 'yes; no; maybe'
            },
        ]

        data = {}
        for _ask in _asks:
            ask_obj = models.Asks(**_ask)
            ask_obj.save()
            data['reply_%s' % ask_obj.pk] = ['Reply for %s' % ask_obj.pk]

        data['social_name'] = [self.invites[0][0]]

        # POST
        response = self.c.post("/feedback360/replies/",
                            data=data)

        replies_jobs = models.Replies.objects()
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(replies_jobs))


class TestFacebookAPIRequests(SimpleTestCase):

    def setUp(self):
        self.token = os.environ.get("TEMPTOKEN")
        if not self.token:
            raise TypeError("You need to configurate environ variable.")

    def test_debug_token(self):
        fb = FacebookAPIRequests()
        res = fb.debug_token(self.token)
        self.assertIn('app_id', res['data'])

    def test_check_app_id(self):
        fb = FacebookAPIRequests()
        self.assertTrue(fb.check_app_id(self.token))

    def test_get_user_public_info(self):
        fb = FacebookAPIRequests()
        res = fb.get_user_public_info(self.token)
        self.assertIn('name', res)
        self.assertIn('email', res)
