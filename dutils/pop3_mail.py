# imports # {{{ 
import html5lib, re, poplib, rfc822
from html5lib import sanitizer
from email import parser
from email.header import decode_header

from django.utils.encoding import smart_unicode
from dutils.signals import new_pop3_mail
# }}} 

mail_re = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')

# print_structure # {{{ 
def print_structure(part, spacer=""):
    print spacer, part.is_multipart(), part.get_content_type()
    if part.is_multipart():
        for subpart in part.get_payload():
            print_structure(subpart, spacer+"    ")
# }}} 

# flatten_mime # {{{ 
def flatten_mime(part):
    parts = []
    if part.is_multipart():
        for subpart in part.get_payload():
            parts += flatten_mime(subpart)
    else:
        parts.append(part)
    return parts
# }}} 

# process_main_part # {{{ 
def process_main_part(main_part):
    parts = flatten_mime(main_part)
    print parts
    if parts[0].get_content_type() == "text/plain":
        text_part = parts[0]
        parts = parts[1:]
    else: text_part = None
    if parts and parts[0].get_content_type() == "text/html":
        html_part = parts[0]
        parts = parts[1:]
    else: 
        html_part = None
    if text_part:
        html = "<pre>%s</pre>" % text_part.get_payload(
            decode=True
        )
    if html_part:
        html = html_part.get_payload(decode=True)
    # NOTE: if html is still not set it indicates something wrong with mail
    return smart_unicode(html, errors="ignore"), parts
# }}} 

# sanitize_html # {{{ 
def sanitize_html(html):
    parser = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
    return parser.parse(html).toxml()
# }}} 

# extract_html_and_attachments # {{{ 
def extract_html_and_attachments(mime_msg):
    if mime_msg.get_content_type() == "multipart/mixed":
        parts = mime_msg.get_payload()
        main_part, attachments = parts[0], parts[1:]
    else:
        main_part, attachments = mime_msg, []

    html, cid_attachments = process_main_part(main_part)
    attachments += cid_attachments
    return html, attachments
# }}} 

# get_mails # {{{
def get_mails(**options):
    print options
    if options["ssl"]:
        pop3 = poplib.POP3_SSL(options["host"], options["port"])
    else:
        pop3 = poplib.POP3(options["host"], options["port"])
    print pop3.getwelcome()
    print pop3.user(options["user"])
    print pop3.pass_(options["password"])
    for i_uid in pop3.uidl()[1][:options["number"]+1]:
        i, uid = i_uid.split()
        message = pop3.retr(i)
        message = "\n".join(message[1])
        message = parser.Parser().parsestr(message)
        message.id = uid
        message.subject = decode_header(message["subject"])[0]
        message.sender = rfc822.parseaddr(message["from"])[1]
        print uid, message["subject"], message["from"], message["date"]
        if not options["leave"]: pop3.dele(i)
        new_pop3_mail.send(sender=pop3, uid=uid, mail=message)
    pop3.quit()
# }}}

# get_attachment_data # {{{ 
def get_attachment_data(attachment):
    content_type = attachment.get_content_type()
    content = attachment.get_payload(decode=True)
    print attachment.items()
    file_name = attachment.get_filename()
    # TODO: try one more attempt for filename
    if not file_name:
        file_name = utils.uuid()
    print file_name
    if "Content-ID" in attachment:
        found_cid = True
        cid = attachment["Content-ID"][1:-1]
    else: cid =""
    return file_name, cid, content_type, content
# }}} 
