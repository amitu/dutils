# imports # {{{
from dutils.whatsup import settings as whatsup_settings
from dutils.whatsup.models import Status

from dutils import utils
# }}}

# perm_required # {{{
def perm_required(perm, view_view=False):
    def paramed_decorator(view):
        def decorated(request, *args, **kw):
            if (
                whatsup_settings.IS_PRIVATE and
                not request.user.has_perm(perm)
            ) or (
                whatsup_settings.IS_PUBLIC and
                not view_view and
                not request.user.has_perm(perm)
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
@perm_required("whatsup.can_view_status", view_view=True)
def index(request):
    queryset = Status.objects.public()
    if "q" in request.REQUEST:
        queryset = queryset.search(request.REQUEST["q"])
    return utils.object_list(
        request,
        queryset = queryset,
        template_name = "whatsup/index.html",
        template_object_name = "status",
        paginate_by = 10,
        renderer = status_renderer if request.REQUEST.get("json") else None,
    )
# }}}

# show_status # {{{
@perm_required("whatsup.can_view_status", view_view=True)
@utils.templated("whatsup/show_status.html")
def show_status(request, status_id):
    return { 
        "status": utils.get_object_or_404(Status, id=status_id, is_deleted=False)
    }
# }}}
