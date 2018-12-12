from django.conf import settings
from django.contrib.auth.models import User
from django import forms

import pwd
import pam

class PAMAuthentificationBackend:
    supports_interactive_user = False

    def authenticate(self, request, username=None, password=None):
        if pam.authenticate(username, password):
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username)
                user.is_staff = False
                user.is_superuser = False
                gcos = pwd.getpwnam(username).pw_gecos.split(',')
                user.email = gcos[4]
                if len(gcos[0].split(' ')) == 2:
                    user.firstname = gcos[0].split(' ')[0]
                    user.lastname = gcos[0].split(' ')[1]

                user.save()
            return user
        else:
            return None
            #raise forms.ValidationError("Username or password wrong.")

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
