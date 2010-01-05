"""
module to upload content to docstoc.com

Put the following in your settings.py file:

DOCSTOC_APPLICATION_KEY = ""
DOCSTOC_AUTHKEY = ""
DOCSTOC_IV = ""
DOCSTOC_USERNAME = ""
DOCSTOC_PASSWORD = ""
DOCSTOC_MEM_ID = ""
DOCSTOC_MIMETYPES = (
    "application/pdf", "application/msword", "application/vnd.ms-excel", 
    "application/msexcel", "application/powerpoint", "application/rtf", 
    "application/vnd.ms-word", "application/vnd.ms-powerpoint"
)
"""
# imports # {{{ 
from django.conf import settings

from tlslite.utils import Python_AES
import base64, urllib2, urllib
from xml.dom.minidom import parseString
Python_AES.MODE_CBC = 2
# }}} 

# pkcs7_pad # {{{ 
def pkcs7_pad(data, blklen=16):
    if blklen>255:
        raise ValueError, 'illegal block size'
    pad=(blklen-(len(data)%blklen))
    return data+chr(pad)*pad
# }}} 

# get_ticket # {{{ 
def get_ticket():
    crypt = Python_AES.new(
        settings.DOCSTOC_AUTHKEY, Python_AES.MODE_CBC, 
        settings.DOCSTOC_IV
    )
    un = base64.b64encode(
        crypt.encrypt(pkcs7_pad(settings.DOCSTOC_USERNAME))
    )
    crypt = Python_AES.new(
        settings.DOCSTOC_AUTHKEY, Python_AES.MODE_CBC, 
        settings.DOCSTOC_IV
    )
    pw = base64.b64encode(
        crypt.encrypt(pkcs7_pad(settings.DOCSTOC_PASSWORD))
    )
    txml = urllib2.urlopen(
    "http://rest.docstoc.com/authentication/AuthenticateUser?Key=%s&UserName=%s&Password=%s" % ( settings.DOCSTOC_APPLICATION_KEY, un, pw)
    ).read()
    tdom = parseString(txml)
    return tdom.getElementsByTagName("Message")[0].firstChild.data
# }}}

# upload_url # {{{  
def upload_url(url, ticket=None):
    if not ticket: ticket = get_ticket()
    # import pdb; pdb.set_trace() 
    u = "http://rest.docstoc.com/upload/UploadFileFromUrl?Key=%s&Ticket=%s&URL=%s" % (
        settings.DOCSTOC_APPLICATION_KEY, ticket, urllib.quote(url)
    )
    txml = urllib2.urlopen(u).read()
    tdom = parseString(txml)
    return tdom.getElementsByTagName("DocumentId")[0].firstChild.data
# }}} 
