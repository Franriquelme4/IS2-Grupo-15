# Generated by Django 4.1 on 2022-09-27 00:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0009_alter_tablero_fase_tablero'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampoPersonalizado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_cp', models.CharField(max_length=50)),
                ('tipoCampo_cp', models.CharField(max_length=50)),
                ('value_cp', models.JSONField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='sprint',
            name='proyecto_sp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='usuario.proyecto'),
        ),
        migrations.AddField(
            model_name='tipouserstory',
            name='flujo_tipo_us',
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='tipouserstory',
            name='proyecto_tipo_us',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='usuario.proyecto'),
        ),
        migrations.AddField(
            model_name='userstory',
            name='asignadoUsu_us',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='usuario.miembroequipo'),
        ),
        migrations.AddField(
            model_name='userstory',
            name='estadoActual_us',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='userstory',
            name='fechaMod_us',
            field=models.DateField(auto_now=True),
        ),
        migrations.AddField(
            model_name='userstory',
            name='prioridadTec_us',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='userstory',
            name='proyecto_us',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='usuario.proyecto'),
        ),
        migrations.AddField(
            model_name='userstory',
            name='tiempoEstimado_us',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='userstory',
            name='valorNegocio_us',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='userstory',
            name='fechaIni_us',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.DeleteModel(
            name='ProyectoSprint',
        ),
        migrations.AddField(
            model_name='tipouserstory',
            name='campoPer_tipo_us',
            field=models.ManyToManyField(to='usuario.campopersonalizado'),
        ),
    ]
