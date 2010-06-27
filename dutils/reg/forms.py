# imports # {{{ 
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from dutils.utils import RequestForm, log_user_in
# }}} 

# LoginForm # {{{
class LoginForm(RequestForm):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.

    Example usage:
    --------------
        url(r'^login/$',
           "dutils.utils.form_handler",
           {
               'template': 'registration/login.html',
               "form_cls": "dutils.utils.LoginForm",
               "next": "/",
           },
           name='auth_login'
        ),
    """
    username = forms.CharField(label=_("Username"), max_length=30)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def clean_password(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.filter(email=username)[0]
            except IndexError:
                pass
            else:
                username = user.username

        if username and password:
            self.user_cache = authenticate(
                username=username, password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct username and password. Note that both fields are case-sensitive."))

        return password

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache

    def save(self):
        log_user_in(self.user_cache, self.request)
        return "/"
# }}}

