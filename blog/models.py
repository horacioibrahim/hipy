#coding: utf-8

import datetime
import os

from mongoengine import *
from mongoengine.django.auth import User
from django.conf import settings

from blog import slugify
from blog.utils import upload_image_handler

# MongoEngine Connect
connect(settings.DBNAME)


class Category(Document):
    """
    Category must be referenced. It has few values reflect my subjects
    that write in blogs. We'll use it to create the menu.
    """
    name = StringField(max_length=80, required=True, primary_key=True)
    slug = StringField(max_length=120)
    icon = ImageField(size=(64,64, True))
    is_main = BooleanField(default=False)
    anchor = StringField() # useful to id anchor html

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if self.anchor:
            self.anchor = self.anchor.lower()
        else:
            self.anchor = self.name.lower()

        super(Category, self).save(*args, **kwargs)


class Comments(EmbeddedDocument):
    content = StringField()
    name = StringField(max_length=120)
    email = StringField(required=True)
    confirmed_inbox = BooleanField(default=False)


class Post(Document):
    CHOICES_PRIORITY = (
        (1, 'low'),
        (2, 'normal'),
        (3, 'high'),
    )
    title = StringField(max_length=120, required=True)
    subtitle = StringField(max_length=120, default=' ')
    created_at = DateTimeField()
    # TODO: um compound index categories + update_at (descending)
    update_at = DateTimeField(default=datetime.datetime.utcnow())
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    tags = ListField(StringField(max_length=50))
    categories = ListField(ReferenceField(Category)) # main category is first or index 0
    comments = ListField(EmbeddedDocumentField(Comments))
    priority_show = IntField(default=1,
                    min_value=1, max_value=3, choices=CHOICES_PRIORITY,
                    help_text=u'Insert 1, 2, or 3 to define priority: !, !!, !!!')
    published = BooleanField(default=False)
    slug = StringField(required=True) # TODO: Index here

    meta = {'allow_inheritance': True}

    def save(self, *args, **kwargs):
        # forces now() for all updates
        self.update_at = None

        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()

        if not self.slug:
            slug = slugify.slugify(self.title)
            p = Post.objects(slug=slug)

            if not p:
                self.slug = slug
            else:
                number = 1
                temp_slug = None
                while p:
                    temp_slug = '_'.join([slug, str(number)])
                    p = Post.objects(slug=temp_slug)
                    number += 1

                self.slug = temp_slug

        super(Post, self).save(*args, **kwargs)


class TextPost(Post):
    """
    Call method create() to new ImagePost for sure that
    images files will to right place.
    """
    # TODO: Do create a thumbnail of images thumbnail_size=(300,150, True)
    cover = StringField(required=False)  # This is a relative path to MEDIA_URL/cover
    content = StringField() # Body post with html tags

    def create(self, file=None):
        # is possible to make a post without cover/image
        if file is not None:
            self.cover = upload_image_handler(file)
        self.save()


class ImagePost(Post):
    """
    Call method create() to new ImagePost for sure that
    images files will to right place.
    """
    image_url_relative = StringField()

    def create(self, file):
        """
        Put image file in a path, rather in database
        """
        self.image_url_relative = upload_image_handler(file)
        self.save()


class PodcastPost(Post):
    stream_file = FileField() # GridFS


class LinkPost(Post):
    link_url = StringField()

