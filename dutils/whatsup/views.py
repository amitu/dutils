# imports # {{{
from dutils.whatsup import settings as whatsup_settings
from dutils.whatsup.models import Status

from dutils import utils
# }}}

# perm_required # {{{
def perm_required(perm):
    def paramed_decorator(view):
        def decorated(request, *args, **kw):
            if (
                whatsup_settings.IS_PRIVATE and
                not request.user.has_perms(perm)
            ):
                return utils.come_back_after_login(request)
            return view(request, *args, **kw)
        return decorated 
    return paramed_decorator
# }}}

# status_renderer # {{{
def status_renderer(template, context):
    return utils.dump_json(
        status_list=[s.get_json() for s in context["status_list"]],
        pages=context["pages"]
    )
# }}}

# index # {{{
@perm_required("can_view_whatsup_status")
def index(request):
    return utils.object_list(
        request,
        queryset = Status.objects.public(),
        template_name = "whatsup/index.html",
        template_object_name = "status",
        paginate_by = 10,
        renderer = status_renderer if request.REQUEST.get("json") else None,
    )
# }}}

@perm_required("can_delete_whatsup_status")
def delete_status(request): pass

@perm_required("can_view_whatsup_status")
def show_status(request): pass
