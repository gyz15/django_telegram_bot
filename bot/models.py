from django.db import models
from .choice import ACTION_TYPE_CHOICES
from django.forms import ValidationError

# Create your models here.


class TGUser(models.Model):
    first_name = models.CharField(max_length=1024)
    last_name = models.CharField(max_length=1024)
    tg_id = models.IntegerField()
    email = models.EmailField(max_length=254, blank=True)
    current_location = models.ForeignKey(
        'bot.Location', on_delete=models.SET_DEFAULT, default=1)
    current_action = models.ForeignKey(
        'bot.Action', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Location(models.Model):
    name = models.CharField(max_length=1024)
    action_can_be_taken = models.ManyToManyField('bot.Action')

    def __str__(self):
        return self.name


class Action(models.Model):
    action_name = models.CharField(max_length=1024, unique=True)
    action_type = models.CharField(max_length=2, choices=ACTION_TYPE_CHOICES)
    go_to = models.ForeignKey(
        'bot.Location', blank=True, on_delete=models.SET_NULL, null=True)
    end_action_code = models.CharField(
        max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.action_name}'


# todo order button (set_position)
