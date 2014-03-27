#coding: utf-8

import sys
import datetime
import pymongo

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from mongoengine.django.shortcuts import get_document_or_404

from blog import models, forms, postDAO


# Setup to connect server.
# workaround MongoEngine and use pymongo (directly)
db_name = '%s' % (settings.DBNAME)
connection_string = "mongodb://localhost"
connection = pymongo.MongoClient(connection_string)
database = connection[db_name]
collection_post = postDAO.PostDAO(database)


def index(request):
    today = datetime.datetime.now()
    categories = models.Category.objects(is_main=True)[0:5]
    posts = models.Post.objects(published=True,
                                created_at__lte=today)\
                            .order_by('-created_at').limit(6) # TODO index sort

    if request.method == 'POST':
        try:
            terms = request.POST['terms']
            terms = terms.split(" ")
        except:
            terms = None

        try:
            results_all = collection_post.search_text(terms=terms)
        except:
            raise TypeError(u'Problem with collections')

        if terms:
            ts = results_all['stats']['timeMicros'] / 1000.0
            results_all['stats']['timeMicros'] = round(ts, 2)
            return render(request, 'search.html',
                      {'results_all': results_all,
                      'posts': results_all['results'],
                      'stats': results_all['stats']
                      }
            )

    return render(request, 'index.html', {'categories': categories,
                                          'posts': posts})


def my_login(request):
    if request.user.is_authenticated():
        return redirect(reverse("post_add"))

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(reverse("post_add"))
            else:
                pass # account disabled
        else:
            return 'invalid login'

    else:
        pass

    return render(request, 'login.html')


def my_logout(request):
    logout(request)
    return redirect(reverse('homepage'))


def category_posts(request, category_anchor):
    """
    The below anchor of Category can contain #anchor or page (domain/page).
    You could make an query with OR, but the numbers of categories is limited.
    Because __contains is solve for me.

    NOTE(DATABASE): We don't interested to use Index to anchor field
    because Category collection is very small the performance result is no
    significant
    """

    anchor_exists = get_document_or_404(models.Category,
                                        anchor__contains=category_anchor.lower())

    today = datetime.datetime.now()
    # TODO index sort (order_by)
    posts = models.Post.objects(categories=anchor_exists, published=True,
                                created_at__lte=today).order_by('-created_at')

    return render_to_response('posts_by_category.html',
                              {'posts': posts, 'category': anchor_exists})


def post_view(request, slug_title):
    """
    Return a post page (tpl: pages.html)
    """
    slug_title = slug_title.lower()
    post = get_document_or_404(models.Post, slug=slug_title)

    return render_to_response('pages.html', {'post': post})


@login_required
def post_add(request):
    """
    The hub of posts types. "Flat is better than nested."
    """
    form = None
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
    form = forms.UploadImageForm(request.POST, request.FILES, )

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
    form = forms.TextContentForm(request.POST, )

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
        post.categories = models.Category.objects(pk=category) # category
        tags = form.cleaned_data['tags']
        tags = tags.replace(" ", "")
        tags = tags.split(',')
        post.tags = tags # array
        post.priority_show = form.cleaned_data['priority_show']
        post.published = True if form.cleaned_data['published'] == 1 else False
        # TextPost fields
        post.content = form.cleaned_data['content']

        # Optional: schedule a post
        try:
            reschedule = request.POST['reschedule']
        except:
            reschedule = None

        reschedule_check = len(reschedule)

        if reschedule_check > 1:
            res_date = reschedule.split("/")

            if len(res_date) == 3:
                # parse to integer the split array (res_date) with [dd, mm, yy]
                day, month, year = int(res_date[0]), int(res_date[1]), int(
                    res_date[2])
                res_date = datetime.datetime(year, month, day,
                                             12) # 12h because timezone
                post.created_at = res_date
            else:
                messages.warning(request,
                                 u'Wrong with date in reschedule field. Use d,m,y')

        # Optional remake slug
        try:
            remake_slug = request.POST["remake_slug"]
        except:
            remake_slug = None

        if remake_slug is not None:
            post.slug = None

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


def ajax_search(request, term):
    """
    Receives a list or one term for search
    """
    pass



