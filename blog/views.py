#coding: utf-8

from django.core import serializers
from django.shortcuts import render_to_response, render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from mongoengine.django.shortcuts import get_document_or_404

from blog import models
from blog import forms


def index(request):
    categories = models.Category.objects(is_main=True)[0:5]
    return render_to_response('index.html', {'categories': categories})

def category_posts(request, category_anchor):
    '''
    The bellow anchor of Category can contain #anchor or page (domain/page).
    You could make an query with OR, but the numbers of categories is limited.
    Because __contains is solve for me.
    '''
    # Don't have interest to use Index to anchor field because Category collection is very small
    # the performance result is no significant

    anchor_exists = get_document_or_404(models.Category, anchor__contains=category_anchor.lower())

    # TODO: categories in Post need be index (scan all docs in posts with categories = X)
    # TODO: poderia ser um bom indice {published:1, categories: 1}. Better more selectivity {categories:1, published:1}
    posts = models.Post.objects(categories=anchor_exists, published=True).order_by('-created_at')
    return render_to_response('posts_by_category.html', {'posts': posts, 'category': anchor_exists})

def post_view(request, slug_title):

    post = models.Post.objects(slug=slug_title).first()

    if not post:
        post = None
        pass # Todo: return erro 404

    return render_to_response('pages.html', {'post': post})

#@login_required
def post_add(request):
    """
    The hub of posts types. "Flat is better than nested."
    """
    posts = models.Post.objects().order_by('-update_at').limit(20)

    if request.method == 'POST':
        # check what type of post: Text, Image, Podcast, Url
        query_dict = request.POST

        try:
            type_post = query_dict['type_post']
        except:
            type_post = None

        if type_post is not None:
            # Call the type post method
            if type_post == 'TextPost':
                return post_text(request, posts=posts)

            if type_post == 'ImagePost':
                return post_image(request, posts=posts)
        else:
            # TODO: if post not selected
            messages.info(request, u'Nenhum post selecionado!')

    else:
        #TODO: remove forms here.
        form = forms.UploadImageForm()

    return render(request, 'to_post.html', {'form': form, 'posts': posts})

def post_image(request, posts=None):
    """
    Post like Image (rather than Text, Podcast, Link etc)
    """
    form = forms.UploadImageForm(request.POST, request.FILES,)

    if form.is_valid():
        # Save image in MEDIA_ROOT and PATH in model
        post_image = models.ImagePost()
        post_image.title = form.cleaned_data['title']
        post_image.create(request.FILES['image'])
    else:
        raise TypeError(form.errors)

    return render(request, 'to_post.html', {'form': form, 'posts': posts})

def post_text(request, posts=None):
    """
    Post like Text (rather than Image, Podcast, Link etc)
    """
    form = forms.TextContentForm(request.POST,)

    if form.is_valid():
        # Save image in MEDIA_ROOT and PATH in model

        # if exists oid make update. instance with id arg
        oid = form.cleaned_data['oid']
        try:
            # Get the object otherwise create one.
            # you can to use models.MODEL(id='id') will updated BUT (It BAD)
            # BECAUSE you isn't handling an previous existent object and
            # you can't overwriting for example save method in models in it way
            # This the best way is get object like instance of existent document:
            post = models.TextPost.objects(id=oid).first() # (It GOOD)
        except:
            post = models.TextPost()

        # Default fields
        post.title = form.cleaned_data['title']
        post.subtitle = form.cleaned_data['subtitle']
        category = form.cleaned_data['categories']
        post.categories.extend(models.Category.objects(pk=category)) # category
        tags = form.cleaned_data['tags']
        tags = tags.split(',')
        post.tags = tags # array
        post.priority_show = 1
        post.published = True if form.cleaned_data['published'] == 1 else False
        # TextPost fields
        post.content = form.cleaned_data['content']
        post.save()

    else:
        raise TypeError(form.errors)

    return render(request, 'to_post.html', {'form': form, 'posts': posts})

# AJAX GET and POSTS
def ajax_get_post(request, objid):
    """
    Return JOSN post by _id
    """
    post = models.Post.objects(id=objid).first()
    return HttpResponse(post.to_json(), mimetype="text/javascript")