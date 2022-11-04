# Generated by Django 4.1 on 2022-11-03 05:16

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comentario', models.CharField(max_length=1000)),
                ('fecha_creacion', models.DateField(default=datetime.date.today)),
                ('horas', models.IntegerField(null=True)),
            ],
            options={
                'verbose_name': 'comenario',
                'verbose_name_plural': 'comentarios',
                'ordering': ['fecha_creacion'],
            },
        ),
        migrations.DeleteModel(
            name='Comentarios',
        ),
        migrations.AddField(
            model_name='userstory',
            name='finalizado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userstory',
            name='comentario',
            field=models.ManyToManyField(blank=True, to='usuario.comentario'),
        ),
    ]
