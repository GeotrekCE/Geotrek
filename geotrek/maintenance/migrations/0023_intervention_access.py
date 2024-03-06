# Generated by Django 3.2.21 on 2023-12-01 16:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0036_accessmean'),
        ('maintenance', '0022_auto_20230503_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='intervention',
            name='access',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='common.accessmean', verbose_name='Access mean'),
        ),
    ]
