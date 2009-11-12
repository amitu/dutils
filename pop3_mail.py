import html5lib, re
from django.utils.encoding import smart_unicode
from html5lib import sanitizer

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

parser = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
mail_re = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')

# sanitize_html # {{{ 
def sanitize_html(html):
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
