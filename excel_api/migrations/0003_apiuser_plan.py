# Generated by Django 3.1.4 on 2021-01-31 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('excel_api', '0002_auto_20210131_2106'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiuser',
            name='plan',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.RESTRICT, to='excel_api.plan'),
        ),
    ]
