# Generated by Django 3.1.4 on 2020-12-31 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0011_auto_20201231_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='arkstock',
            name='had_changes',
            field=models.BooleanField(default=False),
        ),
    ]