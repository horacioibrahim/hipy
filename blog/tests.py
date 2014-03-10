import os

from django.test import TestCase
from django.test import Client
from django.conf import settings

class BlogTest(TestCase):

    def setUp(self):
        self.c = Client()

    def test_post_image(self):
        """
        Test post image
        """
        asset = os.path.join(settings.BASE_DIR, 'assets', 'press.png')

        with open(asset, 'rb') as fp:
            self.c.post('/post/add/image/', {'title':'Test post by test', 'image': fp})

