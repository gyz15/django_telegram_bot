# Generated by Django 3.1.4 on 2020-12-31 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0010_auto_20201224_1318'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArkStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=1024)),
                ('ticker', models.CharField(blank=True, max_length=30)),
                ('shares', models.IntegerField(blank=True)),
                ('shares_delta', models.IntegerField(blank=True)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=5)),
                ('weight_delta', models.IntegerField(blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='tguser',
            name='tg_id',
            field=models.IntegerField(verbose_name='Telegram ID'),
        ),
        migrations.CreateModel(
            name='ArkFund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=4)),
                ('stocks', models.ManyToManyField(related_name='fund', to='bot.ArkStock')),
            ],
        ),
    ]