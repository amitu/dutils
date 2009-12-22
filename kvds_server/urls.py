from django.conf.urls.defaults import *

# urls # {{{
urlpatterns = patterns('dutils.kvds_server.views',
    (r'^start-session/$', 'start_session'),
    (r'^kvds/$', 'kvds'),
    (r'^single/$', 'single'),
    (r'^session/$', 'session'),
    (r'^prefix/$', 'prefix'),
    (r'^$', 'index'),
)
# }}}
