# Generated by Django 3.0.7 on 2020-12-20 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_auto_20201220_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='go_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.Location'),
        ),
    ]
