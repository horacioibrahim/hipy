# coding=utf-8

from django import forms
from models import Post

class PostForm(forms.Form):
    oid = forms.CharField(required=False)
    title = forms.CharField(Post.title.max_length)
    subtitle = forms.CharField(Post.subtitle.max_length, required=False)
    categories = forms.CharField()
    tags = forms.CharField(required=False)
    priority_show = forms.IntegerField(max_value=3, min_value=1)
    published = forms.IntegerField(required=False)

    # TODO: Criar heranças para uploadimageform e textcontentform


class UploadImageForm(PostForm):
    image = forms.ImageField()

    # Access image as request.FILES['image'] (if the form contain enctype="multipart/form-data")
    # para manipular imagens não vamos precisar usar chunks, pois serão menores que 2.5MB
    # mas nos videos e podcasts pode ser necessário usar chunks para não carregar tudo na memória
    # e sentar o servidor. Ver docs.djangoproject.../file-uploads/


class TextContentForm(PostForm):
    cover = forms.ImageField(required=False)
    content = forms.CharField()

