from django.contrib import admin
from .models import TGUser, Location, Action
from django.contrib.auth.models import User, Group
from .forms import ActionAdminForm, TGUserAdminForm
# Register your models here.

admin.site.unregister(Group)
admin.site.unregister(User)
# todo set user all field readonly
# todo edit action type in action admin


class ActionAdmin(admin.ModelAdmin):
    list_display = ('action_name',)
    form = ActionAdminForm


class TGUserAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    form = TGUserAdminForm


admin.site.register(TGUser, TGUserAdmin)
admin.site.register(Location)
admin.site.register(Action, ActionAdmin)
