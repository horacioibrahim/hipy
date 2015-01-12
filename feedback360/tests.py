# -*- coding: utf-8 -*-
from django.test import Client, RequestFactory, SimpleTestCase
from django.contrib.auth.models import AnonymousUser
from mongoengine.queryset import DoesNotExist

# APP
from blog import models as blog_models
from . import models, views, forms
from main.utils import relative_path_url


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

class TestClientTestFeedback360(SimpleTestCase):
    """
        Tests that behaves like user in browser.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.c = Client()

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
                    data={'social_name':'Gilson Filho', 'email':'gbo@gm.com'})

        template_name = response.templates[0].name
        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_name, 'feedback360/thanks_for_interest.html')

    def test_access_control_invited(self):
        # test if access control to invited
        social_name = 'Gilson Filho'
        email = 'gbo@gm.com'
        proximity = 2
        # change invite ... created in backward test_
        invite = models.Invite.objects.get(social_name=social_name.lower())
        invite.interested = False
        invite.save() # invitation created
        #
        response = self.c.post("/feedback360/access/",
                    data={'social_name': social_name, 'email': email})

        #template_name = response.templates[0].name # redirect effects
        relative_path = relative_path_url(response.url)
        participant = models.Participant.objects.get(email=email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual('/feedback360/replies/', relative_path)
        #self.assertEqual(template_name, 'feedback360/replies.html')
        self.assertIsInstance(participant, models.Participant)

    def test_access_control_invited_participant_replies_False(self):
        social_name = 'Gilson Filho'
        email = 'gbo@gm.com'
        response = self.c.post("/feedback360/access/",
                    data={'social_name': social_name, 'email': email})

        relative_path = relative_path_url(response.url)
        participant = models.Participant.objects.get(email=email)
        self.assertEqual('/feedback360/replies/', relative_path)
        self.assertIsInstance(participant, models.Participant)
        self.assertEqual(response.status_code, 302)

    def test_access_control_invited_participant_replies_True(self):
        social_name = 'Gilson Filho'
        email = 'gbo@gm.com'
        participant = models.Participant.objects.get(email=email)
        participant.sent_replies = True
        participant.save()
        response = self.c.post("/feedback360/access/",
                    data={'social_name': social_name, 'email': email})

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
                          'proximity': 2})
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




