import os
from unittest import skip

from django.test import Client, SimpleTestCase
from django.conf import settings
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from bson import ObjectId
from django_ses import SESBackend

from blog.models import User, Category
from blog.views import check_token


class BlogTest(SimpleTestCase):

    def setUp(self):
        email='test_XXX@test.com'
        self.c = Client()
        self.user = User().create_user(username=email,
                                    password='123', email=email)

    def tearDown(self):
        self.user.delete()
        pass

    @skip("Don't want test")
    def test_view_post_image(self):
        """
        Test post image
        """
        asset = os.path.join(settings.BASE_DIR, 'assets', 'press.png')

        with open(asset, 'rb') as fp:
            self.c.post('/post/add/image/', {'title':'Test post by test', 'image': fp})

    def test_put_category_to_user(self):
        """ Test put category or categories for users
        """
        response = self.user.put_category('Startups')
        self.assertEqual(1, response, msg='Test adding category')

    def test_put_category_to_array_as_list(self):
        """ Test put category or categores for users with input
        as list
        """
        response = self.user.put_category(['Startups', 'Lifehacker'])
        self.assertEqual(1, response, msg='Test adding category')

    def test_delete_category(self):
        pass

    def test_view_follower_many_category(self):
        """ Test if can create a new user and to follow many categories
        """
        querystring = {'categories': ['Startups', 'Projects'],
                       'email': self.user.email}
        response = self.c.post(reverse('follower'), querystring)
        # Test response view
        self.assertEqual(response.content, 'true')
        count = User.objects().count()
        categories_persisted = User.objects().skip(count - 1).first().categories
        # Test persistence is right
        self.assertListEqual(querystring['categories'], categories_persisted)

    def test_view_follower_one_category(self):
        """ Test if can create a new user and to follow one category
        """
        querystring = {'categories': ['Startups'],
                       'email': self.user.email}
        response = self.c.post(reverse('follower'), querystring)
        # Test response view
        self.assertEqual(response.content, 'true')
        count = User.objects().count()
        categories_persisted = User.objects().skip(count - 1).first().categories
        # Test persistence is right
        self.assertListEqual(querystring['categories'], categories_persisted)

    def test_create_username_based_objectid(self):
        """ Test if username and emails are different
        """
        self.assertNotEqual(self.user.username, self.user.email)

    def test_clean_username(self):
        self.user.username = 'somebody@example.com'
        pre_username = str(self.user.id)[5:9] + str(self.user.id)[-4:]
        clean_username = self.user.clean_username()
        self.assertEqual(clean_username, pre_username)

    def test_create_user_is_active_false(self):
        self.assertFalse(self.user.is_active)

    def test_check_token(self):
        # Test confirmation page (flow) to check_token
        c = Category(name='Startups', anchor='startups', slug='startups')
        c.save()
        token = self.user.make_token()
        response = self.c.get(reverse('check_token', args=(token,)))
        # test success page
        self.assertEqual(200, response.status_code)
        # test database active account
        user_updated = User.objects.get(token=token)
        # after checking it must change is_active=True
        self.assertTrue(user_updated.is_active)
        # test mistake token
        fail_token = '3qr-07351e93832137ccba45'
        response = self.c.get(reverse('check_token', args=(fail_token,)))
        self.assertEqual(404, response.status_code)
        # test already confirmation
        response = self.c.get(reverse('check_token', args=(token,)))
        self.assertEqual(302, response.status_code)

    @skip # to avoid this options for all tests
    def test_send_mail(self):
        message = EmailMessage('Test Message', 'Body test message',
                               settings.DEFAULT_FROM_EMAIL,
                               [settings.AWS_SES_RETURN_PATH],
                               headers = {'Reply-To': settings.AWS_SES_RETURN_PATH})
        sender = SESBackend()
        result = sender.send_messages([message])
        self.assertEqual(1, result)

    def test_make_token(self):
        token = self.user.make_token()
        self.assertEqual(token, default_token_generator.make_token(self.user))
