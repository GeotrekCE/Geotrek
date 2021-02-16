# Generated by Django 3.1.6 on 2021-02-16 14:12

from django.db import migrations
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20210126_0956'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topology',
            name='paths',
        ),
        migrations.AlterField(
            model_name='pathaggregation',
            name='path',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='aggregations', to='core.path', verbose_name='Path'),
        ),
        migrations.AlterField(
            model_name='pathaggregation',
            name='topo_object',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='aggregations', to='core.topology', verbose_name='Topology'),
        ),
    ]
