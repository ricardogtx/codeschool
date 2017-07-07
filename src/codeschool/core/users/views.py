from django import http
from django.contrib.auth import authenticate, login, logout as do_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _
from rest_framework import viewsets

from codeschool import settings
from . import bricks
from . import models
from . import serializers
from .forms import LoginForm, UserForm, ProfileForm

from codeschool.core.users.models import Profile, User
from django.core.mail import EmailMessage

from django.urls import reverse


#
# REST endpoints
#
class UserViewSet(viewsets.ModelViewSet):
    """
    Active users in the Codeschool platform.
    """

    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer


#
# Auth views
#
def logout(request):
    ctx = {
        'post': request.method == 'POST',
    }

    if request.method == 'POST' and not request.user.is_anonymous():
        do_logout(request)
    return render(request, 'users/logout.jinja2', ctx)


@login_required
def current_user_profile(request):
    user = request.user
    profile = user.profile
    name = profile

    context = dict(
        content_title=_('Profile: {name}').format(name=name),
        content_body=bricks.profile(profile),
        navbar=bricks.navbar(user),
    )
    return render(request, 'base.jinja2', context)


@login_required
def edit_profile(request):

    ctx = login_context()

    instance = Profile.objects.get(user=request.user)

    ctx['profile_form'] = profile_form = ProfileForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        if profile_form.is_valid():
            with transaction.atomic():
                profile_form.save()

        redirect_url = request.GET.get('redirect', 'index')
        return redirect(redirect_url)

        # Redirect
    else:
        return render(request, 'users/profile-edit.jinja2', ctx)


@login_required
def change_password(request, pk):
    user = User.objects.filter(pk=pk)
    link = reverse('password_reset_recover')
    email = EmailMessage(
        'Alteracao de senha',
        'Ola, se deseja alterar sua senha clique em { % url "password_reset_recover" % }',
        'fazzolino29@gay.com',
        [user[0].email],
    )
    email.send(fail_silently=False)
    print(email.message())
    redirect_url = request.GET.get('redirect', 'index')
    return redirect(redirect_url)


@login_required
def change_email(request, pk):
    raise NotImplementedError


@login_required
def user_profile(request, pk):
    """
    View other user's profile.
    """
    raise NotImplementedError


#
# Login page
#
def start(request):
    """
    Handles GET request to the main /login/ url and redirect POSTs to the
    correct view function.
    """

    if request.method == 'POST':
        action = request.POST['action']
        if action == 'login':
            return post_login_form(request)
        elif action == 'register':
            return post_register_form(request)
        else:
            return http.HttpResponseBadRequest('invalid action')

    else:
        return render(request, 'users/start.jinja2', login_context())


def post_login_form(request):
    """
    Handles a POST request via login form.
    """

    ctx = login_context()
    ctx['login_form'] = form = LoginForm(request.POST)

    if form.is_valid():
        # Login
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(**form.cleaned_data)
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[-1])

        # Redirect
        redirect_url = request.GET.get('redirect', 'index')
        return redirect(redirect_url)
    else:
        return render(request, 'users/start.jinja2', ctx)


def post_register_form(request):
    """
    Handles a POST request via the signup form.
    """

    ctx = login_context()
    ctx['user_form'] = user_form = UserForm(request.POST)
    ctx['profile_form'] = profile_form = ProfileForm(request.POST)
    ctx['active_tab'] = 'register'

    if user_form.is_valid() and profile_form.is_valid():
        with transaction.atomic():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.id = user.id
            profile.user = user
            profile.save()

        user = authenticate(**user_form.cleaned_data)
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[-1])

        # Redirect
        redirect_url = request.GET.get('redirect', 'index')
        return redirect(redirect_url)
    else:
        return render(request, 'users/start.jinja2', ctx)


def login_context():
    return dict(
        active_tab='login',
        login_form=LoginForm(),
        user_form=UserForm(),
        profile_form=ProfileForm(),
    )
