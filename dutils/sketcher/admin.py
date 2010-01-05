# imports # {{{
from django.contrib import admin

from dutils.sketcher.models import Context, Page
# }}}

admin.site.register(Context, admin.ModelAdmin)
admin.site.register(Page, admin.ModelAdmin)
