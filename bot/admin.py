from django.contrib import admin
from .models import TGUser, Location, Action
from django.contrib.auth.models import User, Group
# Register your models here.

admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(TGUser)
admin.site.register(Location)
admin.site.register(Action)
