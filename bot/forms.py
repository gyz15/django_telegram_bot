from django import forms
from bot.models import Action, TGUser
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError


class ActionAdminForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if self.cleaned_data['action_type'] == "GO" and self.cleaned_data['go_to'] == None:
            raise ValidationError(_("Go To Action should have Location"))
        elif self.cleaned_data['action_type'] != "GO" and self.cleaned_data['go_to'] != None:
            raise ValidationError(_("Cannot set location if action is not go"))
        return cleaned_data


class TGUserAdminForm(forms.ModelForm):
    class Meta:
        model = TGUser
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['current_action'] != None:
            if cleaned_data['current_action'].action_type == 'GO':
                raise ValidationError(
                    _("Go function cannot be a current action"))
        else:
            pass
        return cleaned_data
