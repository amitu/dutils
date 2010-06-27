# imports # {{{
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.conf import settings

from registration.models import RegistrationProfile # TODO: assimilate this.
# }}}

# send_activation_mail # {{{
def send_activation_mail(user):
    registration_profile = RegistrationProfile.objects.filter(user=user)[0]
    current_site = Site.objects.get_current()
    subject = render_to_string(
        'registration/activation_email_subject.txt',
        { 'site': current_site }
    )
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string(
        'registration/activation_email.txt',
        {
            'activation_key': registration_profile.activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'site': current_site 
        }
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
# }}}

# resend_confirmation_code # {{{
@login_required
def resend_confirmation_code(request):
    if request.method == "POST":
        send_activation_mail(request.user)
        return HttpResponseRedirect(request.path + "?sent=true")
    return render_to_response(
        "registration/resend_confirmation_code.html",
        { "site": Site.objects.get_current() },
        context_instance=RequestContext(request)
    )
# }}}
