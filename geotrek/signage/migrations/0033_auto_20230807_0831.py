# Generated by Django 3.2.20 on 2023-08-07 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signage', '0032_alter_line_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinePictogram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_insert', models.DateTimeField(auto_now_add=True, verbose_name='Insertion date')),
                ('date_update', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Update date')),
                ('pictogram', models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogram')),
                ('label', models.CharField(blank=True, default='', max_length=250, verbose_name='Label')),
                ('code', models.CharField(blank=True, default='', max_length=250, verbose_name='Code')),
                ('description', models.TextField(blank=True, help_text='Complete description', verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Line pictogram',
                'verbose_name_plural': 'Line pictograms',
            },
        ),
        migrations.AddField(
            model_name='line',
            name='pictograms',
            field=models.ManyToManyField(blank=True, related_name='lines', to='signage.LinePictogram', verbose_name='Pictograms'),
        ),
    ]
