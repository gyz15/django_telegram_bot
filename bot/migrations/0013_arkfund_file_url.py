# Generated by Django 3.1.4 on 2020-12-31 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0012_arkstock_had_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='arkfund',
            name='file_url',
            field=models.URLField(default='cron-job.com'),
            preserve_default=False,
        ),
    ]