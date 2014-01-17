from django.contrib import admin
from myapp.models import *

admin.site.register(Users)
admin.site.register(File_mapping)
admin.site.register(Media_item)
admin.site.register(Ad_item)
admin.site.register(Original_media_item)
admin.site.register(Original_ad_item)