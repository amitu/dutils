# imports # {{{ 
from django.utils import simplejson
from django.conf import settings
from django import forms
from django.core.files.base import ContentFile
from django.utils.encoding import smart_str, smart_unicode
from django.http import HttpResponseServerError, HttpResponseRedirect
from django.http import HttpResponse

import time, random, re, os, sys, traceback
from hashlib import md5
import urllib2, urllib, threading
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
def create_logger(name=None):
    if name is None:
        name = settings.APP_DIR.namebase
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(
        settings.APP_DIR.joinpath("%s.log" % name)
    )
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
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
        response = "%s\n" % exc_type.__name__
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
        error_type.__name__, error_value
    )
    for i in tb_list:
        s += "\n" + i
    return s
# }}} 

# S3 Photo Storeage # {{{
def delete_jpg(key):
    if settings.USE_S3_BACKEND:
        conn = boto.connect_s3(
            settings.S3_ACCOUNT, settings.S3_KEY
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
    salt = random.randint(0, 1000)
    full_key = "%s/%s.gif" % (key, salt)
    if settings.USE_S3_BACKEND:
        conn = boto.connect_s3(
            settings.S3_ACCOUNT, settings.S3_KEY
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
    s = cStringIO.StringIO()
    img.convert("RGB").save(s, format=format)
    s.seek(0)
    salt = random.randint(0, 1000)
    full_key = "%s/%s.%s" % (key, salt, format)

    if getattr(settings, "USE_S3_BACKEND", False):
        conn = boto.connect_s3(
            settings.S3_ACCOUNT, settings.S3_KEY
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
def get_content_from_path(p):
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
    else:
        return urllib2.urlopen(p).read()
#}}}

# send_html_mail # {{{
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from smtplib import SMTP
import email.Charset

from stripogram import html2text
from feedparser import _sanitizeHTML

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
    to be used when length of seq is known.
    makes one slice call per batch, in case of django db api this is faster
    """

    for i in range(0, len(seq), batch_size):
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

