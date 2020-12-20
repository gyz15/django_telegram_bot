from django.contrib import admin
from .models import TGUser, Location, Action
from django.contrib.auth.models import User, Group
# Register your models here.

admin.site.unregister(Group)
admin.site.unregister(User)
# todo set user all field readonly
# todo edit action type in action admin

admin.site.register(TGUser)
admin.site.register(Location)
admin.site.register(Action)
