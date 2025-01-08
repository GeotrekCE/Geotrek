from django.db import migrations, models
from django.conf import settings
from geotrek.sensitivity.models import SensitiveArea, Species


def generate_name(apps, schema_editor):
    """Populate SensitiveAreas name from Species"""

    sensitive_area = SensitiveArea
    languages = settings.MODELTRANSLATION_LANGUAGES
    update_fields = [
        "name",
    ]
    update_fields += [f"name_{lang}" for lang in languages]
    for row in sensitive_area.objects.existing().filter(species__category=2):
        for field in update_fields:
            setattr(row, field, getattr(row.species, field))
        row.save(update_fields=update_fields)
        for field in update_fields:
            print(f"species.manager {row.species._meta.managers}")
            print(f"row {row.species} | field {field}")
            setattr(row.species, field, "")
        row.species.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("sensitivity", "0028_alter_sensitivearea_structure"),
    ]

    operations = [
        migrations.AddField(
            model_name="sensitivearea",
            name="name",
            field=models.CharField(default="", max_length=250, verbose_name="Name"),
        ),
        # migrations.RunPython(update_translation_fields_func, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(generate_name, reverse_code=migrations.RunPython.noop),
    ]
