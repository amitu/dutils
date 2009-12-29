# imports # {{{ 
from django.utils import simplejson
from django.conf import settings
from django import forms
from django.core.files.base import ContentFile
from django.utils.encoding import smart_str, smart_unicode
from django.http import HttpResponseServerError, HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import force_unicode
from django.http import HttpResponse, Http404
from django.core.urlresolvers import get_mod_func
from django.template.defaultfilters import filesizeformat
from django.utils.functional import Promise
from django.db.models.query import QuerySet

import time, random, re, os, sys, traceback
from hashlib import md5
import urllib2, urllib, threading, cgi
from PIL import Image

import logging
import cStringIO
try:
    import solr
except ImportError: 
    print "solr lib required for some functions"
# }}} 

# threaded_task # {{{ 
def threaded_task(func):
    def decorated(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    decorated.__doc__ = func.__doc__
    decorated.__name__ = func.__name__
    return decorated
# }}} 

# logging # {{{
def create_logger(name=None, level=logging.DEBUG):
    if name is None:
        name = settings.APP_DIR.namebase
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(
        settings.APP_DIR.joinpath("%s.log" % name)
    )
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(level)
    return logger

logger = create_logger()

class PrintLogger(object): 
    def __init__(self, old_out):
        self.old_out = old_out

    def write(self, astring): 
        logger.debug(astring)
        self.old_out.write(astring)

#sys.stdout = PrintLogger(sys.stdout)
# }}}

# SimpleExceptionHandler www.djangosnippets.org/snippets/650/ # {{{
class SimpleExceptionHandler:
    def process_exception(self, request, exception):
        import sys, traceback
        (exc_type, exc_info, tb) = sys.exc_info()
        response = "%s\n" % getattr(exc_type, "__name__", exc_type)
        response += "%s\n\n" % exc_info
        response += "TRACEBACK:\n"    
        for tb in traceback.format_tb(tb):
            response += "%s\n" % tb
        logger.exception(exception)    
        logger.info(request.POST)
        logger.info(request.GET)
        logger.info(request.META)
        logger.info(request.COOKIES)
        if not settings.DEBUG: return
        if not request.is_ajax(): return
        return HttpResponseServerError(response)
# }}}

# uuid # {{{ 
def uuid( *args ):
  """
    Generates a universally unique ID.
    Any arguments only create more randomness.
  """
  t = long( time.time() * 1000 )
  r = long( random.random()*100000000000000000L )
  try:
    a = socket.gethostbyname( socket.gethostname() )
  except:
    # if we can't get a network address, just imagine one
    a = random.random()*100000000000000000L
  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
  data = md5(data).hexdigest()
  return data
# }}}  

# solr related functions # {{{ 
def solr_add(**data_dict):
    s = solr.SolrConnection(SOLR_ROOT)
    s.add(**data_dict)
    s.commit()
    s.close()

def solr_delete(id):
    s = solr.SolrConnection(SOLR_ROOT)
    s.delete(id)
    s.commit()
    s.close()

def solr_search(
    q, fields=None, highlight=None, score=True, 
    sort=None, sort_order="asc", **params
):
    s = solr.SolrConnection(SOLR_ROOT)
    response = s.query(
        q, fields, highlight, score, sort, sort_order, **params
    )
    return response

def solr_paginator(q, start,rows):
    response = {}
    conn = solr.SolrConnection(SOLR_ROOT)
    res = conn.query(q)
    numFound = int(res.results.numFound)
    results = res.next_batch(start=start,rows=rows).results
    response['results'] = [dict(element) for element in results]
    response['count'] = numFound
    response['num_found'] = len(response['results'])
    response['has_prev'] = True
    response['has_next'] = True
    if start <= 0:
        response['has_prev'] = False
    if (start + rows) >= numFound:
        response['has_next'] = False
    return response
# }}}

# solr_time # {{{
def solr_time(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
# }}}

# request context preprocessor # {{{ 
def context_preprocessor(request):
    d = {}
    d["path"] = request.path
    return d
# }}}

# RequestForm # {{{ 
class RequestForm(forms.Form):
    def __init__(self, request, *args, **kw):
        super(RequestForm, self).__init__(*args, **kw)
        self.request = request
# }}} 

# profane words # {{{ 
class SacredField(forms.CharField):
    def clean(self, value):
        value = super(SacredField,self).clean(value)
        value_words = re.split('\W+', value)
        for word in kvds(key="profane_words")["profane_words"].split(","):
            for val_word in value_words:
                if(val_word == word):
                    raise forms.ValidationError("%s is not an allowed word." % val_word)
        return value

class SacredANField(forms.CharField):
    def clean(self, value):
        value = super(SacredField,self).clean(value)
        value_words = re.split('\W+', value)
        for word in kvds(key="profane_words")["profane_words"].split(","):
            for val_word in value_words:
                if(val_word == word):
                    raise forms.ValidationError("%s is not an allowed word." % val_word)
        pattern = "^[a-zA-Z\s]+$"
        match = re.match(pattern, value)
        if not match:
            raise forms.ValidationError("Special characters not allowed.")
        return value.strip()
# }}} 

# resize_image # {{{
def resize_image(image, thumb_size, square, format):
    #img.seek(0) # see http://code.djangoproject.com/ticket/8222 for details
    #image = Image.open(img)
    
    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
        
    # get size
    thumb_w, thumb_h = thumb_size
    # If you want to generate a square thumbnail
    #if thumb_w == thumb_h:
    if square:
        # quad
        xsize, ysize = image.size
        # get minimum size
        minsize = min(xsize,ysize)
        # largest square possible in the image
        xnewsize = (xsize-minsize)/2
        ynewsize = (ysize-minsize)/2
        # crop it
        image2 = image.crop(
            (xnewsize, ynewsize, xsize-xnewsize, ysize-ynewsize)
        )
        # load is necessary after crop                
        image2.load()
        # thumbnail of the cropped image (ANTIALIAS to make it look better)
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    else:
        # not quad
        image2 = image
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    
    io = cStringIO.StringIO()
    # PNG and GIF are the same, JPG is JPEG
    if format.upper()=='JPG':
        format = 'JPEG'
    
    image2.save(io, format)
    return Image.open(ContentFile(io.getvalue()))    
# }}}

# crop_imgae # {{{
def crop_image(img, x, y, w, h):
    #image.seek(0)
    #img = Image.open(image)
    box = (x, y, x+w, y+h)
    region = img.crop(box)
    io = cStringIO.StringIO()
    region.save(io, img.format)
    return Image.open(ContentFile(io.getvalue()))
# }}}

# ext_add # {{{
def ext_add(value,add):
    p = os.path.splitext(value)
    return p[0] + add + p[1]
# }}}

# process_image # {{{
def process_image(image_name, photo, x, y, w, h, size=(58,72)):
    cropped_image = crop_image(photo,x,y,w,h)
    final_image = resize_image(cropped_image,size, False, 'JPEG')
    return update_jpg(img=final_image, key=image_name)
# }}}

# clear_unicode # {{{ 
def clear_unicode(object):
    if type(object) == type({}):
        return dict(
            [(str(k), v) for k, v in object.items()]
        )
    else:
        return object
# }}} 

# formatExceptionInfo # {{{ 
def formatExceptionInfo(level = 6):
    error_type, error_value, trbk = sys.exc_info()
    tb_list = traceback.format_tb(trbk, level)   
    s = "Error: %s \nDescription: %s \nTraceback:" % (
        getattr(error_type, "__name__", error_type), error_value
    )
    for i in tb_list:
        s += "\n" + i
    return s
# }}} 

# S3 Photo Storeage # {{{
def delete_jpg(key):
    import boto
    if settings.USE_S3_BACKEND:
        conn = boto.connect_s3(
            settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY
        )
        bucket_1 = conn.create_bucket(settings.S3_BUCKET_1)
        bucket_2 = conn.create_bucket(settings.S3_BUCKET_2)
        # delete old key
        for k in itertools.chain(
            bucket_1.get_all_keys(prefix=key + "/"), 
            bucket_2.get_all_keys(prefix=key + "/"),
        ): k.bucket.delete_key(k.key)
    else: pass # we dont care about local storage cleanup. Lazy me.

def update_gif(key, data):
    import boto
    from boto.s3.key import Key
    salt = random.randint(0, 1000)
    full_key = "%s/%s.gif" % (key, salt)
    if settings.USE_S3_BACKEND:
        conn = boto.connect_s3(
            settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY
        )
        bucket_1 = conn.create_bucket(settings.S3_BUCKET_1)
        bucket_2 = conn.create_bucket(settings.S3_BUCKET_2)
        # create new data
        bucket = random.choice((bucket_1, bucket_2))
        k = Key(bucket)
        k.key = full_key 
        k.set_contents_from_string(data)
        k.set_acl("public-read")
        return "http://%s/%s" % (bucket.name, full_key)
    else:
        # we dont do random stuff for local storage. Lazy me.
        full_key = "%s/%s.gif" % (key, salt)
        # create folders
        parent = settings.MEDIA_ROOT.joinpath(full_key).parent
        if not parent.exists(): parent.makedirs()
        file(
            settings.MEDIA_ROOT.joinpath(full_key), "wb"
        ).write(data)
        return "/static/%s" % full_key

def update_jpg(key, img, delete_key=None, format="jpeg"):
    import boto
    from boto.s3.key import Key
    s = cStringIO.StringIO()
    img.convert("RGB").save(s, format=format)
    s.seek(0)
    salt = random.randint(0, 1000)
    full_key = "%s/%s.%s" % (key, salt, format)

    if getattr(settings, "USE_S3_BACKEND", False):
        conn = boto.connect_s3(
            settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY
        )
        bucket_1 = conn.create_bucket(settings.S3_BUCKET_1)
        bucket_2 = conn.create_bucket(settings.S3_BUCKET_2)
        # delete old key
        for key_to_delete in [key, delete_key]:
            if not key_to_delete: continue
            for k in itertools.chain(
                bucket_1.get_all_keys(prefix=key_to_delete + "/"), 
                bucket_2.get_all_keys(prefix=key_to_delete + "/"),
            ): k.bucket.delete_key(k.key)
        # create new data
        bucket = random.choice((bucket_1, bucket_2))
        k = Key(bucket)
        k.key = full_key 
        k.set_contents_from_file(s)
        k.set_acl("public-read")
        return "http://%s/%s" % (bucket.name, full_key)
    else:
        # we dont do random stuff for local storage. Lazy me.
        full_key = "%s/%s.%s" % (key, salt, format)
        # create folders
        parent = settings.UPLOAD_DIR.joinpath(full_key).parent
        if not parent.exists(): parent.makedirs()
        file(
            settings.UPLOAD_DIR.joinpath(full_key), "wb"
        ).write(s.read())
        return "/static/uploads/%s" % full_key
# }}}

# get_content_from_path #{{{
def get_content_from_path(p, data=None, number_of_tries=1):
    if (
        p.startswith("http://") or 
        p.startswith("ftp://") or 
        p.startswith("https://")
    ):
        exceptions = []
        for i in range(number_of_tries):
            try:
                if data:
                    return urllib2.urlopen(p, data).read()
                else:
                    return urllib2.urlopen(p).read()
            except Exception, e:
                exceptions.append(e)
        # we are still here, meaning we had exception thrice
        raise exceptions[0]
    if settings.APP_DIR.joinpath(p).exists():
        return file(
            settings.APP_DIR.joinpath(p), 'rb'
        ).read()
    elif settings.APP_DIR.joinpath("../../../").joinpath(p[1:]).exists():
        return file(
            settings.APP_DIR.joinpath("../../../").joinpath(p[1:]), 'rb'
        ).read()
    elif settings.APP_DIR.joinpath(p[1:]).exists():
        return file(
            settings.APP_DIR.joinpath(p[1:]), 'rb'
        ).read()
    raise IOError
#}}}

# send_html_mail # {{{
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from smtplib import SMTP
import email.Charset

from dutils.messaging import messenger

charset='utf-8'

email.Charset.add_charset(charset, email.Charset.SHORTEST, None, None)

# send_html_mail = messenger.send_html_mail
@threaded_task
def send_html_mail(
    subject, sender="support@fwd2tweet.com", recip="", context=None, 
    html_template="", text_template="", sender_name="",
    html_content="", text_content="", recip_list=None, sender_formatted=""
):
    from stripogram import html2text
    from feedparser import _sanitizeHTML

    if not context: context = {}
    if html_template:
        html = render(context, html_template)
    else: html = html_content
    if text_template:
        text = render(context, text_template)
    else: text = text_content
    if not text:
        text = html2text(_sanitizeHTML(html,charset))        

    if not recip_list: recip_list = []
    if recip: recip_list.append(recip)

    try:
        server = SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        if settings.EMAIL_USE_TLS:
            server.ehlo()
            server.starttls()
            server.ehlo()
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            server.login(
                settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD
            )
    except Exception, e: 
        print e
        return
    
    if not sender_formatted:
        sender_formatted = "%s <%s>" % (sender_name, sender) 

    for recip in recip_list:
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = subject.encode("utf8", 'xmlcharrefreplace')
        msgRoot['From'] = sender_formatted.encode(
            "utf8", 'xmlcharrefreplace'
        )
        msgRoot['To'] = recip.encode("utf8", 'xmlcharrefreplace')
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        msgAlternative.attach(MIMEText(smart_str(text), _charset=charset))
        msgAlternative.attach(
            MIMEText(smart_str(html), 'html', _charset=charset)
        )

        try:
            server.sendmail(sender, recip, msgRoot.as_string())
        except Exception, e: print e

    server.quit()

def render(context, template):
    from django.template import loader, Context
    if template:
        t = loader.get_template(template)
        return t.render(Context(context))
    return context
# }}}

# IndianMobileField # {{{
class IndianMobileField(forms.CharField):
    def clean(self, value):
        value = super(IndianMobileField,self).clean(value)
        pattern = "^[0-9\s]+$"
        match = re.match(pattern, value)
        if not match:
            raise forms.ValidationError("Numaric input expected.")
        if len(value) != 10:
            raise forms.ValidationError("Incomplete number found.")
        if value[0] != "9":
            raise forms.ValidationError("Invalid mobile number.")
        return value.strip()
# }}}

# facebook related helpers # {{{ 
# fb_ensure_session_valid # {{{
def fb_ensure_session_valid(request):
    signature_hash = fb_get_signature(request.COOKIES, True)
    assert signature_hash == request.COOKIES[settings.FB_API_KEY]
# }}}

# fb_get_signature # {{{
def fb_get_signature(values_dict, is_cookie_check=False):
    signature_keys = []
    for key in sorted(values_dict.keys()):
        if (is_cookie_check and key.startswith(settings.FB_API_KEY + '_')):
            signature_keys.append(key)
        elif (is_cookie_check is False):
            signature_keys.append(key)

    if (is_cookie_check):
        signature_string = ''.join(
            [
                '%s=%s' % (
                    x.replace(settings.FB_API_KEY + '_',''), values_dict[x]
                )
                for x in signature_keys
            ]
        )
    else:
        signature_string = ''.join(
            ['%s=%s' % (x, values_dict[x]) for x in signature_keys]
        )
    signature_string = signature_string + settings.FB_API_SECRET

    return md5(signature_string).hexdigest()
# }}} 

# fb_get_user_info # {{{
def fb_get_user_info(request, *args):
    get_user_info_data = {
        'method':'Users.getInfo',
        'api_key': settings.FB_API_KEY,
        'session_key': request.COOKIES[settings.FB_API_KEY + '_session_key'],
        'call_id': time.time(),
        'v': '1.0',
        'uids': request.COOKIES[settings.FB_API_KEY + '_user'],
        'fields': ",".join(args),
        'format': 'json',
    }
    get_user_info_hash = fb_get_signature(get_user_info_data)
    get_user_info_data["sig"] = get_user_info_hash
    get_user_info_params = urllib.urlencode(get_user_info_data)
    get_user_info_response = urllib2.urlopen(
        settings.FB_REST_SERVER, get_user_info_params
    ).read()
    return simplejson.loads(get_user_info_response)
# }}} 

# fb_get_uid # {{{
def fb_get_uid(request):
    return request.COOKIES[settings.FB_API_KEY + '_user']
# }}}
# }}} 

# JSONResponse # {{{
class JSONResponse(HttpResponse):
    def __init__(self, data):
        HttpResponse.__init__(
            self, content=simplejson.dumps(data),
            #mimetype="text/html",
        ) 
# }}}

# batch_gen # {{{
def batch_gen1(seq, batch_size):
    """ 
    Usage:

    >>> batch_gen1(range(10), 3)
    ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9,))
    to be used when length of seq is known.
    makes one slice call per batch, in case of django db api this is faster
    """

    if isinstance(seq, QuerySet): #4739, not everything django is pragmatic
        length = seq.count()
    else:
        length = len(seq)
    for i in range(0, length, batch_size):
        yield seq[i:i+batch_size]

def batch_gen2(seq, batch_size):
    """ to be used when length is not known """
    it = iter(seq)
    while True:
        values = ()
        for n in xrange(batch_size):
            values += (it.next(),)
    yield values
# }}}

# cacheable # {{{ 
def cacheable(cache_key, timeout=3600):
    """ Usage:

    class SomeClass(models.Model):
        # fields [id, name etc]

        @cacheable("SomeClass_get_some_result_%(id)s")
        def get_some_result(self):
            # do some heavy calculations
            return heavy_calculations()

        @cacheable("SomeClass_get_something_else_%(name)s")
        def get_something_else(self):
            return something_else_calculator(self)
    """
    from django.core.cache import cache
    def paramed_decorator(func):
        def decorated(self):
            key = cache_key % self.__dict__
            if cache.has_key(key):
                return cache[key]
            res = func(self)
            cache.set(key, res, timeout)
            return res
        decorated.__doc__ = func.__doc__
        decorated.__dict__ = func.__dict__
        return decorated 
    return paramed_decorator
# }}} 

# stales_cache # {{{ 
def stales_cache(cache_key):
    """ Usage:

    class SomeClass(models.Model):
        # fields
        name = CharField(...)

        @stales_cache("SomeClass_some_key_that_depends_on_name_%(name)")
        @stales_cache("SomeClass_some_other_key_that_depends_on_name_%(name)")
        def update_name(self, new_name):
            self.name = new_name
            self.save()
    """
    from django.core.cache import cache
    def paramed_decorator(func):
        def decorated(self, *args, **kw):
            key = cache_key % self.__dict__
            cache.delete(key)
            return func(self, *args, **kw)
        decorated.__doc__ = func.__doc__
        decorated.__dict__ = func.__dict__
        return decorated
    return paramed_decorator
# }}} 

# ajax_validator  # {{{
def ajax_validator(request, form_cls):
    """
    Usage
    -----

    # in urls.py have something like this:
    urlpatterns = patterns('',
        # ... other patterns
        (
            r'^ajax/validate-registration-form/$', 'ajax_validator',
            { 'form_cls': 'myproject.accounts.forms.RegistrationForm' }
        ),
    )

    # sample javascript code to use the validator
    $(function(){
        $("#id_username, #id_password, #id_password2, #id_email").blur(function(){
            var url = "/ajax/validate-registration-form/?field=" + this.name;
            var field = this.name;
            $.ajax({
                url: url, data: $("#registration_form").serialize(),
                type: "post", dataType: "json",    
                success: function (response){ 
                    if(response.valid)
                    {
                        $("#"+field+"_errors").html("Sounds good");
                    }
                    else
                    {
                        $("#"+field+"_errors").html(response.errors);
                    }
                }
            });
        });
    });
    """
    mod_name, form_name = get_mod_func(form_cls)
    form_cls = getattr(__import__(mod_name, {}, {}, ['']), form_name)
    form = form_cls(request.POST)
    if "field" in request.GET: 
        errors = form.errors.get(request.GET["field"])
        if errors: errors = errors.as_text()
    else:
        errors = form.errors
    return JSONResponse(
        { "errors": errors, "valid": not errors }
    ) 
# }}}

# SizeAndTimeMiddleware # {{{ 
class SizeAndTimeMiddleware(object):
    """
    Usage:

    Used for showing size of the page in human readable format and time
    taken to generate the page on the server. To use it, in your base
    template, somewhere put the line:

    <!-- ____SIZE_AND_DATE_PLACEHOLDER____ -->

    May be used on production.
    """
    def process_request(self, request):
        request._request_start_time = time.time() 

    def process_response(self, request, response):
        if not hasattr(request, "_request_start_time"): return response
        if response['Content-Type'].split(';')[0] in (
            'text/html', 'application/xhtml+xml'
        ):
            response.content = smart_unicode(response.content).replace(
                "<!-- ____SIZE_AND_DATE_PLACEHOLDER____ -->", 
                "(%s, %0.3f seconds)" % (
                    filesizeformat(len(response.content)),
                    time.time() - request._request_start_time,
                )
            )
        return response
# }}} 

# LazyEncoder # {{{ 
class LazyEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        else:
            return super(LazyEncoder, self).default(o)
# }}} 

# form_handler # {{{
def form_handler(
    request, form_cls, require_login=False, block_get=False,
    next=None, template=None, login_url=None, 
):
    """
    Some ajax heavy apps require a lot of views that are merely a wrapper
    around the form. This generic view can be used for them.
    """
    from django.shortcuts import render_to_response
    if login_url is None: 
        login_url = getattr(settings, "LOGIN_URL", "/login/")
    if callable(require_login): 
        require_login = require_login(request)
    elif require_login:
        require_login = not request.user.is_authenticated()
    if require_login:
        if require_login == "404":
            raise Http404("login required")
        return HttpResponseRedirect(
            "%s?next=%s" % (login_url, request.path)
        )
    if block_get and request.method != "POST":
        raise Http404("only post allowed")
    if isinstance(form_cls, basestring):
        # can take form_cls of the form: "project.app.forms.FormName"
        from django.core.urlresolvers import get_mod_func
        mod_name, form_name = get_mod_func(form_cls)
        form_cls = getattr(__import__(mod_name, {}, {}, ['']), form_name)
    if next: assert template, "template required when next provided"
    if template and request.method == "GET":
        return render_to_response(
            template, {"form": form_cls(request)}, 
            context_instance=RequestContext(request)
        )
    form = form_cls(request, request.REQUEST)
    if form.is_valid():
        saved = form.save()
        if next: return HttpResponseRedirect(next)
        if template: return HttpResponseRedirect(saved)
        return JSONResponse({ 'success': True, 'response': saved })
    if template:
        return render_to_response(
            template, {"form": form}, 
            context_instance=RequestContext(request)
        )
    return JSONResponse({ 'success': False, 'errors': form.errors })
# }}}

# copy_file_to_s3 # {{{ 
s3_operation_lock = threading.Condition(threading.Lock())
def copy_file_to_s3(p, key, bucket):
    from boto.s3.key import Key
    final_url = "http://%s/%s" % (bucket.name, key)

    k = Key(bucket)
    k.key = key 
    k.set_contents_from_string(get_content_from_path(p))
    k.set_acl("public-read")

    return final_url
# }}} 

# cleaned_data # {{{
def clean_data(func):
    def decorated(self, *args, **kw):
        d = self.cleaned_data.get
        return func(self, d(func.__name__[6:]), d, *args, **kw)
    decorated.__doc__ = func.__doc__
    decorated.__dict__ = func.__dict__
    decorated.__name__ = func.__name__
    return decorated
# }}}

# get address book from google # {{{


class GContacts(object):
    
    def __init__(self, email, password):
        import gdata.contacts
        self.gd_client = gdata.contacts.service.ContactsService()
        self.gd_client.email = email
        self.gd_client.password = password
        self.gd_client.source = 'Your Application Name'
        self.gd_client.ProgrammaticLogin()

    def ListAllContacts(self):
        """Retrieves a list of contacts and displays name and primary email."""
        feed = self.gd_client.GetContactsFeed()
        contacts = []

        while feed:
            for f in feed.entry:
                for e in f.email:
                    if f.title.text:
                        contacts.append({ f.title.text:e.address })
                    else:
                        contacts.append({ e.address:e.address })
            next = feed.GetNextLink()
            feed = None
            if next:
                feed = self.gd_client.GetContactsFeed(next.href)
        return contacts

def get_google_contacts(request):
    import gdata.contacts.service
    gservice = GContacts(
        email = request.GET['email'], 
        password = request.GET['password']
    )
    next = request.GET["next"]
    try:
        contacts = gservice.ListAllContacts()
        request.session["contact_feed"] = contacts
        return HttpResponseRedirect(next)
    except gdata.service.BadAuthentication:
        return HttpResponse('Authentication Error, Login Password mismatch')
#}}}

# get address book from yahoo # {{{
def get_yahoo_contacts(request):
    import time
    import hashlib
    import urllib
    from xml.etree.ElementTree import ElementTree
    import xml.etree.ElementTree
    import urllib2
    from django.utils import simplejson

    appid = settings.YAHOO_APPID
    secret = settings.YAHOO_SECRET_KEY
    if request.GET.get('appid'):
        token = request.GET['token']
        ts = int(time.time())
        sig = hashlib.md5("/WSLogin/V1/wspwtoken_login?appid=%s&token=%s&ts=%s%s" % (appid, token, ts, secret)).hexdigest()
        url = "https://api.login.yahoo.com/WSLogin/V1/wspwtoken_login?appid=%s&token=%s&ts=%s&sig=%s" % (appid, token, ts, sig)
        u = urllib.urlopen(url)
        data = u.read()
        data = data.replace(':',"_")
        tree = ElementTree()
        b = xml.etree.ElementTree.fromstring(data)
        cookie = b.getchildren()[0].find('Cookie').text
        wssid = b.getchildren()[0].find('WSSID').text
        headers = {'Cookie': cookie.strip()}
        url = "http://address.yahooapis.com/v1/searchContacts?format=json&WSSID=%s&appid=%s&token=%s" % (wssid, appid, token)
        req = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(req)
        addressbook = []
        data = simplejson.loads(response.read())
        for contact in data['contacts']:
            email, name = '',''
            for cf in contact['fields']:
                if cf['type'] == 'email':
                    email = cf.get('data','')
                if cf['type'] == 'name':
                    name = "%s %s" % (cf.get('first',''), cf.get('last',''))
                if cf['type'] == 'yahooid':
                    email = cf.get('data','') + "@yahoo.com"
            if email or name:
                addressbook.append({name:email})
        return HttpResponse("OK GETTING APID")

    appdata = "foobar"
    ts = int(time.time())
    sig = hashlib.md5("/WSLogin/V1/wslogin?appid=%s&appdata=%s&ts=%s%s" % (appid, appdata, ts, secret)).hexdigest()
    url = "https://api.login.yahoo.com/WSLogin/V1/wslogin?appid=%s&appdata=%s&ts=%s&sig=%s" % (appid, appdata, ts, sig)
    return HttpResponseRedirect(url)

#}}}

"""
template helpers
----------------
data profiles: eg registration with error
    stored in db as json
all templates in templates folder
case: data profile to template mapping
"""

# attrdict # {{{ 
class attrdict(dict):
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__dict__ = self
# }}} 

# get_url_with_params # {{{
def get_url_with_params(request, path_override=None, without=None):
    if path_override: path = path_override
    else: path = request.path
    querystring = request.META.get("QUERY_STRING")
    if not querystring: querystring = ""
    query_dict = dict(cgi.parse_qsl(querystring))
    if without and without in query_dict:
        del query_dict[without]
    querystring = urllib.urlencode(query_dict)
    if querystring:
        return "%s?%s&" % ( path, querystring )
    else:
        return "%s?" % path
#}}}

# mail_exception # {{{
def mail_exception(tag="django"):
    from django.core import mail
    mail.mail_admins(
        "exception in %s" % tag, formatExceptionInfo(12), 
    )
# }}}

