#coding: utf-8

import datetime
import os
from mongoengine import *
from main.settings import DBNAME
from django.conf import settings

import slugify

connect(DBNAME)

def upload_image_handler(f):
    # Save to path MEDIA_ROOT
    image_to_save = os.path.join(settings.MEDIA_ROOT, f.name)
    with open(image_to_save, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    image_url_relative = ''.join([settings.MEDIA_URL, os.path.basename(destination.name)])
    return image_url_relative


class User(Document):
    username = StringField(unique=True, primary_key=True)
    email = EmailField(required=True)
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)
    is_author = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now())


class Category(Document):
    name = StringField(max_length=80, required=True, primary_key=True)
    slug = StringField(max_length=120)
    icon = ImageField(size=(64,64, True))
    is_main = BooleanField(default=False)
    anchor = StringField() # useful to id anchor html

    def save(self, *args, **kwargs):
        if self.anchor:
            self.anchor = self.anchor.lower()
        else:
            self.anchor = self.name.lower()

        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

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
    update_at = DateTimeField(default=datetime.datetime.now()) # TODO: um compound index categories + update_at (descending)
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    tags = ListField(StringField(max_length=50))
    categories = ListField(ReferenceField(Category)) # main category is first or index 0
    comments = ListField(EmbeddedDocumentField(Comments))
    priority_show = IntField(default=1, min_value=1, max_value=3, choices=CHOICES_PRIORITY, help_text=u'Insert 1, 2, or 3 to define priority: !, !!, !!!')
    published = BooleanField(default=False)
    slug = StringField(required=True) # TODO: Index here

    meta = {'allow_inheritance': True}

    def save(self, *args, **kwargs):
        # forces now() for all updates
        self.update_at = None

        if not self.created_at:
            self.created_at = datetime.datetime.now()

        # a post make isn't someone with too frequently
        # because to check if exits slug is not problem
        if not self.slug:
            slug = slugify.slugify(self.title)
            p = Post.objects(slug=slug)

            if not p:
                self.slug = slug
            else:
                number = 1

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
    # largura boa no cover pode ser 660 por 330 (full)
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

    # image = BinaryField() # I trust that better is archive in file system
    # BinaryField e GridFS é para arquivos que não serão acessados
    # constantemente pelo mesmo usuário os quais podem ficar em cache. Mas para
    # vídeos, áudio e download do tipo um ebook, etc. pode ser excelente.
    # APP: no meu caso as pessoas poderão voltar ao post várias vezes e a
    # imagem não estará em cache um outro problema para o blog é que as imagens
    # serão com mais de 32KB e no IE8 isso é um limitador ver mais:
    # The "data" URI scheme RFC2397

    # Overwrite save() this model to put image on MEDIA_ROOT
    # directory or anything info (ex.: filename, contentType, etc.)
    def create(self, file):
        self.image_url_relative = upload_image_handler(file)
        self.save()


class PodcastPost(Post):
    stream_file = FileField() # GridFS


class LinkPost(Post):
    link_url = StringField()

