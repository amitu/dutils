# based on django.templates.loaders.filesystem
# imports # {{{
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.utils._os import safe_join

from dutils.shpaml import convert_text
# }}}

# get_template_sources # {{{
def get_template_sources(template_name, template_dirs=None):
    if not template_dirs:
        template_dirs = getattr(settings, "SHPAML_TEMPLATE_DIRS", [])
    print template_dirs
    for template_dir in template_dirs:
        try:
            print safe_join(template_dir, template_name)
            yield safe_join(template_dir, template_name)
        except ValueError:
            # The joined path was located outside of template_dir.
            pass
# }}}

# load_template_source # {{{
def load_template_source(template_name, template_dirs=None):
    tried = []
    print "load_template_source.shpaml_loader", template_name, template_dirs
    for filepath in get_template_sources(template_name, template_dirs):
        try:
            return (convert_text(open(filepath).read().decode(settings.FILE_CHARSET)), filepath)
        except IOError:
            tried.append(filepath)
    if tried:
        error_msg = "Tried %s" % tried
    else:
        error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
    raise TemplateDoesNotExist, error_msg
# }}}

load_template_source.is_usable = True
