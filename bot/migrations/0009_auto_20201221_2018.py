# Generated by Django 3.0.7 on 2020-12-21 12:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0008_action_end_action'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='end_action',
            new_name='end_action_code',
        ),
    ]