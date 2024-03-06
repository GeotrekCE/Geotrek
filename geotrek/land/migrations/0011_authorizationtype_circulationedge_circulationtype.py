# Generated by Django 3.2.20 on 2023-09-26 14:56

from django.db import migrations, models
import django.db.models.deletion
import mapentity.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20230503_0837'),
        ('authent', '0011_alter_userprofile_structure'),
        ('land', '0010_auto_20230503_0837'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorizationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('structure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='authent.structure', verbose_name='Related structure')),
            ],
            options={
                'verbose_name': 'Authorization type',
                'verbose_name_plural': 'Authorization types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CirculationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('structure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='authent.structure', verbose_name='Related structure')),
            ],
            options={
                'verbose_name': 'Circulation type',
                'verbose_name_plural': 'Circulation types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CirculationEdge',
            fields=[
                ('topo_object', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.topology')),
                ('eid', models.CharField(blank=True, max_length=1024, verbose_name='External id')),
                ('authorization_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='land.authorizationtype', verbose_name='Authorization type')),
                ('circulation_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='land.circulationtype', verbose_name='Circulation type')),
            ],
            options={
                'verbose_name': 'Circulation edge',
                'verbose_name_plural': 'Circulation edges',
            },
            bases=(mapentity.models.DuplicateMixin, 'core.topology', models.Model),
        ),
    ]
