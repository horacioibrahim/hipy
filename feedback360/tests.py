from django.test import Client
from mongoengine.queryset import DoesNotExist

# APP
from . import models
from main.simpletest import mongotest

class TestFeedback360(mongotest.MongoTestCase):
    def setUp(self):
        email = 'horacio@gmail.com'
        social_name = 'Horacio Ibrahim'
        proximity = 0
        i = models.Invite()
        i.email = email
        i.social_name = social_name
        i.proximity = proximity
        i.save()
        self.invite = i

    def tearDown(self):
        #self.invite.delete()
        pass

    def test_invited_was_invited(self):
        name = 'Horacio Ibrahim'
        check_invite = models.Invite.was_invited(name)
        self.assertTrue(check_invite)
        # not invited
        check_not_invited = models.Invite.was_invited('Not Invited')
        self.assertFalse(check_not_invited)

    def test_invited_set_interested(self):
        models.Invite.set_interested('Mario Lago',
                                                'mlago@gmail.com')
        obj = models.Invite.objects.get(social_name='Mario Lago',
                                        interested=True)
        self.assertIsInstance(obj, models.Invite)
        self.assertEqual(obj.social_name, 'Mario Lago')

    def test_invited_is_interested(self):
        check_interest = models.Invite().is_interested(name='Mario Lago')
        self.assertTrue(check_interest)
        check_interest = models.Invite().is_interested(email='mlago@gmail.com')
        self.assertTrue(check_interest)
        check_interest = models.Invite().is_interested(email='pocoyo@pc.com')
        self.assertFalse(check_interest)

    def test_participant_save(self):
        email = 'horacio@gmail.com'
        social_name = 'Horacio Ibrahim'
        participant = models.Participant(name=social_name, email=email)
        obj = participant.save()
        self.assertIsInstance(obj, models.Participant)

    def test_participant_create_not_invited(self):
        name='Anna Lelis'
        email='annale@m.co'
        participant = models.Participant(name=name, email=email)
        #obj = participant.save()
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

class TestClientTestFeedback360(mongotest.MongoTestCase):

    def setUp(self):
        self.c = Client()

    def validate_invitation(self):
        self.c.post('/feedback360/validate/', data={'email':'horacio@gmail.com',
                                            'social_name':'Horacio Ibrahim'})
