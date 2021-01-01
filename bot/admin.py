from django.contrib import admin
from .models import TGUser, Location, Action, ArkStock, ArkFund
from django.contrib.auth.models import User, Group
from .forms import ActionAdminForm, TGUserAdminForm
# Register your models here.

admin.site.unregister(Group)
admin.site.unregister(User)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('action_name', 'action_type', 'is_developing')
    list_editable = ('action_type', 'is_developing')
    form = ActionAdminForm


class TGUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tg_id', 'email', 'is_developer')
    readonly_fields = ('first_name', 'last_name', 'tg_id', 'email')
    form = TGUserAdminForm


admin.site.register(TGUser, TGUserAdmin)
admin.site.register(Location)
admin.site.register(Action, ActionAdmin)
admin.site.register(ArkFund)
admin.site.register(ArkStock)
