# Generated by Django 3.0.7 on 2020-12-20 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_action_action_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_name',
            field=models.CharField(max_length=1024, unique=True),
        ),
    ]
