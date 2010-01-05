from django.conf.urls.defaults import *

urlpatterns = patterns('dgci.views',
    url(r'^contacts/google/$', 'utils.get_google_contacts'),
    url(r'^contacts/yahoo/$', 'utils.get_yahoo_contacts'),
)

