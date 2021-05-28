# Generated by Django 3.1.13 on 2021-08-02 13:58

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0013_auto_20210121_0943'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachedMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('author', models.CharField(max_length=300)),
                ('content', models.TextField()),
                ('suricate_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='Identifiant')),
                ('type', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='report',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2021, 1, 1, 12, 0, tzinfo=utc), verbose_name='Creation date'),
        ),
        migrations.AddField(
            model_name='report',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2021, 1, 1, 12, 0, tzinfo=utc), verbose_name='Last updated'),
        ),
        migrations.AddField(
            model_name='report',
            name='locked',
            field=models.BooleanField(default=False, verbose_name='Locked'),
        ),
        migrations.AddField(
            model_name='report',
            name='origin',
            field=models.CharField(default='unknown', max_length=100, verbose_name='Origin'),
        ),
        migrations.AddField(
            model_name='report',
            name='uid',
            field=models.UUIDField(blank=True, null=True, unique=True, verbose_name='Identifiant'),
        ),
        migrations.AddField(
            model_name='reportstatus',
            name='suricate_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Identifiant'),
        ),
        migrations.AlterField(
            model_name='reportactivity',
            name='suricate_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='Suricate id'),
        ),
        migrations.AlterField(
            model_name='reportproblemmagnitude',
            name='suricate_id',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='Suricate id'),
        ),
        migrations.CreateModel(
            name='ReportAttachedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=500)),
                ('suricate_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='Identifiant')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feedback.report')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageAttachedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=500)),
                ('suricate_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='Identifiant')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feedback.attachedmessage')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='attachedmessage',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feedback.report'),
        ),
    ]
