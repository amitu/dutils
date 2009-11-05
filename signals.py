import django.dispatch

new_pop3_mail = django.dispatch.Signal(providing_args=["uid", "mail"])
