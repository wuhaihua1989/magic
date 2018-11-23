from django.contrib import admin
from apps.users.models import *
# Register your models here.
admin.site.register(Industry)
admin.site.register(Professions)
admin.site.register(User)
admin.site.register(CustomPermission)
admin.site.register(Address)
admin.site.register(Menu)
admin.site.register(RoleMenu)
admin.site.register(Permission)