#coding: utf-8

import sys
import datetime
import pymongo
import re
import doctest
from json import loads, dumps
from random import randint

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.template import loader, Context
from mongoengine.django.shortcuts import get_document_or_404
from mongoengine.document import NotUniqueError

from . import models, forms, postDAO
from .utils import do_syntax_html
from tasks.tasks import task_send_simple_email


# Setup to connect server.
# workaround MongoEngine and use pymongo (directly)
db_name = None
def set_db_name():
    global db_name
    for db_name_value, db_alias in settings.MONGO_DATABASES.items():
        db_name = db_name_value
        break # once time
set_db_name()
connection_string = "mongodb://localhost"
connection = pymongo.MongoClient(connection_string)
database = connection[db_name]
collection_post = postDAO.PostDAO(database)


def index(request):
    today = datetime.datetime.now()
    categories = models.Category.objects(is_main=True)[0:5]
    posts = models.Post.objects(published=True,
                                created_at__lte=today) \
        .order_by('-created_at').limit(6) # TODO index sort

    # if request.method == 'POST':
    orig_terms = None
    try:
        terms = request.GET['terms']
        orig_terms = terms
        terms = re.findall(r"[\w]+", terms)
    except:
        terms = None

    if terms:

        try:
            results_all = collection_post.search_text(terms=terms)
        except:
            raise TypeError(u'Problem with collections')

        ts = results_all['stats']['timeMicros'] / 100000.0
        results_all['stats']['timeMicros'] = round(ts, 2)
        orig_terms = " ".join(terms)
        return render(request, 'search.html', {'results_all': results_all,
                                               'posts': results_all[
                                                   'results'],
                                               'stats': results_all[
                                                   'stats'],
                                               'terms': orig_terms,
        }
        )

    return render(request, 'index.html',
                  {'categories': categories, 'posts': posts})

def query_posts(request):
    today = datetime.datetime.now()
    posts = models.Post.objects(published=True,
            created_at__lte=today).order_by('-created_at').skip(6).limit(20)

    return render(request, 'includes/posts_inject.html', dict(posts=posts))

def educacao_map(request):
    return render(request, 'education_br.html')

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
            return HttpResponse('Invalid login (username or password)')

    else:
        pass

    return render(request, 'login.html')


def my_logout(request):
    logout(request)
    return redirect(reverse('homepage'))

def follower(request):
    """ Method to save followers of blog. It receives selected categories by POST
    and put categories in user profile (a mongoengine User subclass).
    Return True in case success rather False.
    """
    response = False
    new_u = None
    if request.method == "POST":
        categories = request.POST.getlist('categories', None)
        if not categories:
            categories = request.POST.getlist('categories[]', None) # mysterious[]<-
        email = request.POST['email']
        u = models.User()

        try:
            new_u = u.create_user(username=email, email=email, password=None)
            new_u.put_category(categories)
            response = True
        except NotUniqueError:
            response = False
        except:
            raise

        if response:
            body = '''
            Olá,
            Recebi seu interesse no projeto hipy. Agora, somente preciso que
            você confirme o seu email pelo link abaixo:
            Link: %s

            Deixo um sincero abraço e desejo-lhe liberdade de conhecimento!

            ass: Horacio Ibrahim
            '''
            token = new_u.make_token()
            link = reverse('check_token', args=(token,))
            body_linked = body % ("".join([settings.BASE_URL, link]))
            task_id = task_send_simple_email.delay('Confirmação de Cadastro - hipy',
                              body_linked, [new_u.email,], headers=None)

    else:
        return redirect(reverse('homepage'))

    return HttpResponse(dumps(response), content_type=("text", "javascript"))


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
def post_delete(request, oid):
    """
    Delete documents
    """
    if request.user.is_superuser:
        post = get_document_or_404(models.Post, id=oid)
        post.delete()

    return redirect(reverse('post_add'))

@login_required
def post_add(request):
    """
    The hub of posts types. "Flat is better than nested."
    """
    form = None
    categories = None
    posts = models.Post.objects().order_by('-update_at') # unlimited for instance

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
        categories = models.Category.objects()

    return render(request, 'to_post.html', {'form': form, 'posts': posts,
                                            'categories':categories})


def post_image(request, posts=None):
    """
    Post like Image (rather than Text, Podcast, Link etc)
    """
    form = forms.UploadImageForm(request.POST, request.FILES, )

    if form.is_valid():
        # Save image in MEDIA_ROOT and PATH in model
        post_img = models.ImagePost()
        post_img.title = form.cleaned_data['title']
        post_img.create(request.FILES['image'])
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
            # you can to use models.MODEL(id='id') will updated BUT (It's BAD)
            # But you can not handling an previous existent object
            # like overwriting save method in models.
            # The best way is get object like instance of existent document:
            post = models.TextPost.objects.get(id=oid) # (It GOOD)
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
        content = form.cleaned_data['content']
        post.content = do_syntax_html(content)

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
        raise TypeError(form.errors) # Debug

    return render(request, 'to_post.html', {'form': form, 'posts': posts})

def check_token(request, token):
    """Confirm user by token sent by email"""
    categories = models.Category.objects()
    user_by_token = get_document_or_404(models.User, token=token)
    if user_by_token.is_active:
        user_categories = user_by_token.categories
        if len(user_categories) > 0:
            end = len(user_categories) - 1
            aleatory = randint(0, end)
            return redirect(reverse('category_posts', args=(user_by_token.categories[aleatory].lower(),)))
        else:
            end = len(categories) - 1
            aleatory = randint(0, end)
            return redirect(reverse('category_posts', args=(categories[aleatory].slug,)))

    user_by_token.is_active = True

    try:
        user_by_token.save()
        confirmed_db = True
    except:
        raise

    if confirmed_db:
        body = '''
        Obrigado pela confirmação!

        Minha missão nesse projeto é influenciar positivamente a vida das pessoas
        que se relacionam comigo direta ou indiretamente nos tornando, reciprocamente,
        ainda melhores.

        # Saiba mais sobre o projeto hipy.
        http://hipy.co/post/as-metas-e-objetivos-do-hipy/

        Deixo um sincero abraço e desejo-lhe liberdade de conhecimento!

        Horacio Ibrahim
        hipy.co
        '''
        task_id = task_send_simple_email.delay('Obrigado pela confirmação - hipy', body,
                          [user_by_token.email])

    return render(request, 'check_token.html',
                  {'email': user_by_token.email, 'categories':categories})

# AJAX GET and POSTS
def ajax_get_post(request, objid):
    """
    Return JOSN post by _id
    """
    try:
        post = models.Post.objects.get(id=objid)
        output = post.to_json()
    except:
        output = []

    return HttpResponse(output, content_type=("text", "javascript"))


def ajax_search(request, term):
    """
    Receives a list or one term for search
    """
    pass


def get_categories(request):
    """
    Get all categories for user follow it
    """
    # The vex is a plugin to modal dialog. It has many requirements
    # as messages, inputs or buttons attributes. The vex's better
    # is capable of doing faster and easier handles dialog modal rather
    # foundation (zurb).
    # DISCLOSURE: The callback function receive name attribute of inputs
    # if form tags is not exists.
    #
    # e.g:
    # Example 1 - Empty data:
    # <form><input name="name" value="1"></form>
    # callback: function(data) { print data.name } // output Object {}
    #
    # Example 2 - Useful data (without tag <form>):
    # <input name="name" value="1">
    # callback: function(data) { print data.name } // output Object {name: 1}
    #
    # See more Vex: http://github.hubspot.com/vex/api/basic/

    categories = models.Category.objects(is_main=True)
    t = loader.get_template("modal_categories.html")
    c = Context({'categories': categories})

    # Options for Vex.js
    output = {}
    message = u'Marque uma ou mais categorias de interesse:'
    btn_text = {'YES': u'Seguir'}
    options_vex = dict(message=message, btn_text=btn_text, html=t.render(c))

    # Add options of Vex in "queryset" (it's now list)
    output['options_vex'] = options_vex

    return HttpResponse(dumps(output), content_type=("text", "javascript"))
