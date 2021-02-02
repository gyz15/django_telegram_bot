from django.db import models
import string
import random as rd
# Create your models here.


def gen_code():
    pw_len = 20
    choice_of_pw = string.ascii_lowercase + string.ascii_uppercase + string.digits

    while True:
        key = ''.join(rd.choices(choice_of_pw, k=pw_len))
        if ApiUser.objects.filter(key=key).count() == 0:
            break
    return key


class Plan(models.Model):
    name = models.CharField(max_length=100)
    is_unlimited = models.BooleanField(default=False)
    api_per_day = models.IntegerField()

    def __str__(self):
        return f'{self.name}'


class ApiUser(models.Model):
    email = models.EmailField()
    password = models.CharField(max_length=50)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    key = models.CharField(max_length=20, unique=True, default=gen_code)
    call_used_today = models.IntegerField(default=0)
    plan = models.ForeignKey(
        'excel_api.Plan', on_delete=models.RESTRICT, default=2)
    # a function that can generate key

    def __str__(self):
        return f'{self.first_name}'

    @property
    def has_call(self):
        if self.call_used_today + 1 > self.plan.api_per_day and self.plan.is_unlimited == False:
            return False
        return True
