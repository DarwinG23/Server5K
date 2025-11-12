"""Add granular time component fields and populate them from `tiempo` existing values.

Generated manually to add horas/minutos/segundos/milisegundos and a data migration to
fill them for existing records.
"""
from django.db import migrations, models


def populate_time_components(apps, schema_editor):
    RegistroTiempo = apps.get_model('app', 'RegistroTiempo')
    for r in RegistroTiempo.objects.all():
        try:
            total = int(r.tiempo or 0)
        except Exception:
            total = 0
        ms = total % 1000
        total_seconds = total // 1000
        s = total_seconds % 60
        total_minutes = total_seconds // 60
        m = total_minutes % 60
        h = total_minutes // 60
        r.horas = h
        r.minutos = m
        r.segundos = s
        r.milisegundos = ms
        # Update only the new fields to avoid changing other fields or triggers
        r.save(update_fields=['horas', 'minutos', 'segundos', 'milisegundos'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_competencia_options_competencia_en_curso_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrotiempo',
            name='horas',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='registrotiempo',
            name='minutos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='registrotiempo',
            name='segundos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='registrotiempo',
            name='milisegundos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(populate_time_components, reverse_code=migrations.RunPython.noop),
    ]
