# Generated by Django 3.1.4 on 2021-01-01 12:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0020_auto_20210101_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arkstock',
            name='fund',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='bot.arkfund'),
            preserve_default=False,
        ),
    ]
