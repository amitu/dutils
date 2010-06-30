from django.contrib import admin
from dutils.whatsup.models import Status

admin.site.register(Status, admin.ModelAdmin)
