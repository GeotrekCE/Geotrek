# Generated by Django 3.1.4 on 2020-12-18 10:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('outdoor', '0008_auto_20201218_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='level',
            field=models.PositiveIntegerField(default=settings.DEFAULT_STRUCTURE_PK, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='site',
            name='lft',
            field=models.PositiveIntegerField(default=settings.DEFAULT_STRUCTURE_PK, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='site',
            name='rght',
            field=models.PositiveIntegerField(default=settings.DEFAULT_STRUCTURE_PK, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='site',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True, default=settings.DEFAULT_STRUCTURE_PK, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='site',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='outdoor.site', verbose_name='Parent'),
        ),
    ]
