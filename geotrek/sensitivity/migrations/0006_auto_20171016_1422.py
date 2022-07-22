from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sensitivity', '0005_auto_20171016_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensitivearea',
            name='species',
            field=models.ForeignKey(db_column='espece', on_delete=django.db.models.deletion.PROTECT, verbose_name='Species', to='sensitivity.Species'),
        ),
        migrations.AlterField(
            model_name='species',
            name='category',
            field=models.IntegerField(default=settings.DEFAULT_STRUCTURE_PK, verbose_name='Category', editable=False, db_column='categorie', choices=[(1, 'Species'), (2, 'Regulatory')]),
        ),
    ]
