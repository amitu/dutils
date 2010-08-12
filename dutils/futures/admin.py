from django.contrib import admin

from dutils.futures.models import Future

admin.site.register(Future, admin.ModelAdmin)
