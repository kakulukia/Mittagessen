# Generated by Django 4.0.3 on 2022-04-06 18:57

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True)),
                ('deleted', models.DateTimeField(editable=False, null=True)),
                ('concealed', models.BooleanField(default=False, editable=False)),
                ('headline', models.CharField(max_length=300, verbose_name='Name')),
                ('start', models.DateField(verbose_name='Wochenstart')),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'abstract': False,
                'base_manager_name': 'data',
                'default_manager_name': 'data',
            },
            managers=[
                ('data', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='meal',
            options={'base_manager_name': 'data', 'default_manager_name': 'data', 'get_latest_by': 'created', 'ordering': ['-created'], 'verbose_name': 'Mahlzeit', 'verbose_name_plural': 'Mahlzeiten'},
        ),
    ]
