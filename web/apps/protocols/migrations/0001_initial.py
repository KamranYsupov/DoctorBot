# Generated by Django 4.2.1 on 2024-11-29 14:54

from django.db import migrations, models
import django.db.models.deletion
import web.db.model_mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0001_initial'),
        ('doctors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('id', models.CharField(db_index=True, default=web.db.model_mixins.ulid_default, editable=False, max_length=26, primary_key=True, serialize=False, unique=True)),
                ('patient_name', models.CharField(max_length=150, verbose_name='ФИО пациента')),
                ('patient_ulid', models.CharField(db_index=True, max_length=26)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='protocols', to='doctors.doctor', verbose_name='Доктор')),
                ('patient', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='protocols', to='patients.patient', verbose_name='Пациент')),
            ],
            options={
                'verbose_name': 'Протокол',
                'verbose_name_plural': 'Протоколы',
            },
        ),
    ]
