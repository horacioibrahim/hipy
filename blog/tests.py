import os
from unittest import skip

from django.test import Client, SimpleTestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from bson import ObjectId

from blog.models import User


class BlogTest(SimpleTestCase):

    def setUp(self):
        obj = str(ObjectId())
        username = obj[5:9] + obj[-4:]
        self.username = username
        self.c = Client()
        self.user = User().create_user(username=username,
                                    password='123', email='test_XXX@test.com')

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

    def test_view_follower_many_category(self):
        """ Test if can create a new user and to follow many categories
        """
        querystring = {'categories': ['Startups', 'Projects'],
                       'email': self.user.email}
        response = self.c.post(reverse('follower'), querystring)
        # Test response view
        self.assertEqual(response.content, 'True')
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
        self.assertEqual(response.content, 'True')
        count = User.objects().count()
        categories_persisted = User.objects().skip(count - 1).first().categories
        # Test persistence is right
        self.assertListEqual(querystring['categories'], categories_persisted)
