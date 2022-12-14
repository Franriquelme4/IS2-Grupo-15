from email.policy import default
from django.db import models
import datetime
 
# Create your models here.

class Permiso(models.Model):
    """Los permisos se tienen previamente cargados, cada permiso se asiganan a los distintos roles"""
    descripcion_permiso = models.CharField(max_length=100,blank=False,null=False)
    nombre_permiso = models.CharField(max_length=100,blank=False,null=False)
    class Meta:
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['descripcion_permiso']
    def __str__(self):
        return self.descripcion_permiso

class Rol(models.Model):
    """Se agrega la tabla roles para tener un control de todos los roles que tiene un determinado usuario, existen 3 roles ya creados previamente"""
    nombre_rol = models.CharField(max_length=50,blank=False,null=False)
    descripcion_rol = models.CharField(max_length=100,blank=False,null=False)
    permiso = models.ManyToManyField(Permiso)
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['descripcion_rol']
    def __str__(self):
        return self.descripcion_rol
    def getPermisos(self):
        return self.permiso.all()
    def poseePermiso(self,codigo):
        permiso = self.permiso.filter(nombre_permiso=codigo)
        return permiso.count() > 0


class Usuario(models.Model):
    """Modelo de la tabla usuarios, en la cual se almacenan todos los datos del usuario"""
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    nombre_usuario = models.CharField(max_length=100)
    activo = models.BooleanField(default=False)
    df_rol = models.ForeignKey('Rol',on_delete=models.CASCADE,default=2)
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['nombre_usuario']
    def __str__(self):
        return self.nombre_usuario

class MiembroEquipo(models.Model):
    """Modelo de la tabla miembro, en la cual se almacenan todos los datos del cliente"""
    miembro_usuario = models.ManyToManyField(Usuario)
    miembro_rol = models.ManyToManyField(Rol)
    descripcion = models.CharField(max_length=100,default='')
    class Meta:
        verbose_name = 'Miembro'
        verbose_name_plural = 'Miembros'
    def __str__(self):
        return self.descripcion


class Cliente(models.Model):
    """Modelo de la tabla clientes, en la cual se almacenan todos los datos del cliente"""
    nombre_cliente = models.CharField(max_length=100)
    apellido_cliente = models.CharField(max_length=100)
    email_cliente = models.CharField(max_length=100)
    telefono_cliente = models.CharField(max_length=100)
    empresa_cliente = models.CharField(max_length=100)
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre_cliente']
    def __str__(self):
        return self.nombre_cliente

class Estado(models.Model):
    """Tabla en la cual se almacenan todos los estados del proyecto"""
    descripcion = models.CharField(max_length=50,null=False)
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['descripcion']
    def __str__(self):
        return self.descripcion

class Proyecto(models.Model):
    """Modelo de la tabla proyectos, en la cual se almacenan todos los datos del proyecto"""
    nombre_proyecto = models.CharField(max_length=100)
    cliente_proyecto = models.ForeignKey('Cliente',on_delete=models.CASCADE)
    fecha_ini_proyecto = models.DateField(null=True)
    fecha_fin_proyecto = models.DateField(null=True)
    duracion = models.IntegerField(default=0,null=True)
    descripcion_proyecto = models.CharField(max_length=100,default='')
    miembro_proyecto = models.ManyToManyField('MiembroEquipo')
    sprint_dias = models.IntegerField(default=0)
    fecha_creacion = models.DateField(default=datetime.date.today)
    estado = models.ForeignKey('Estado',on_delete=models.CASCADE)
    sprint_actual = models.ForeignKey('Sprint',on_delete=models.CASCADE,null=True)
    historial = models.ManyToManyField('Historial')
    class Meta:
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering = ['nombre_proyecto']
    def __str__(self):
        return self.nombre_proyecto

class ProyectoRol(models.Model):
    """Se almacenan los roles por proyecto"""
    rol = models.ManyToManyField('Rol')
    proyecto = models.ManyToManyField('Proyecto')
    descripcion_proyecto_rol = models.CharField(max_length=100,default='')
    class Meta:
        verbose_name = 'ProyectoRol'
        verbose_name_plural = 'ProyectoRoles'
    def __str__(self):
        return self.rol

class CampoPersonalizado(models.Model):
    nombre_cp = models.CharField(max_length=50,null=False)
    tipoCampo_cp = models.CharField(max_length=50,null=False)
    value_cp = models.JSONField(null=True)

class TipoUserStory(models.Model):
    """Modelo de la tabla tipo de user story, en la cual se almacenan todos los datos de los tipos de user story"""
    proyecto_tipo_us  = models.ForeignKey('Proyecto',on_delete=models.CASCADE,null=True)
    prioridad_tipo_us = models.ForeignKey('PrioridadTUs',on_delete=models.CASCADE,null=True)
    nombre_tipo_us = models.CharField(max_length=50,null=False)
    descripcion_tipo_us = models.CharField(max_length=100,null=False)
    flujo_tipo_us = models.JSONField(null=True)
    campoPer_tipo_us = models.ManyToManyField('CampoPersonalizado')
    fecha_creacion = models.DateField(default=datetime.date.today)
    class Meta:
        verbose_name = 'Tipo User Story'
        verbose_name_plural = 'Tipos de User Story'
        ordering = ['nombre_tipo_us']
    def __str__(self):
        return self.nombre_tipo_us

class TipoUs_Proyecto(models.Model):
    proyecto = models.ForeignKey('Proyecto',on_delete=models.CASCADE,null=True)
    tipoUs = models.ForeignKey('TipoUserStory',on_delete=models.CASCADE,null=True)

class UserStory(models.Model):
    """Modelo de la tabla user story, en la cual se almacenan todos los datos de los user story"""
    proyecto_us = models.ForeignKey('Proyecto',on_delete=models.CASCADE,null=True)
    nombre_us = models.CharField(max_length=50,null=False)
    descripcion_us = models.CharField(max_length=50,null=False)
    tiempoEstimado_us = models.IntegerField(null=True)
    disponible = models.BooleanField(default=True)
    estadoActual_us = models.CharField(max_length=20,null=True)
    tiempoTrabajado = models.IntegerField(default=0)
    tipo_us = models.ForeignKey('TipoUserStory',on_delete=models.CASCADE)
    asignadoUsu_us = models.ForeignKey('MiembroEquipo',on_delete=models.CASCADE,null=True)
    fechaIni_us = models.DateField(auto_now_add=True)
    fechaMod_us = models.DateField(auto_now=True)
    fecha_creacion = models.DateField(default=datetime.date.today)
    prioridad_negocio = models.IntegerField(default=0)
    prioridad_tecnica = models.IntegerField(default=0)
    prioridad_sprint = models.IntegerField(default=0)
    prioridad_final = models.IntegerField(default=0)
    fase = models.ForeignKey('Fase',on_delete=models.CASCADE,null=True)
    comentario = models.ManyToManyField('Comentario',blank=True)
    finalizado = models.BooleanField(default=False)
    class Meta:
        verbose_name = 'User Story'
        verbose_name_plural = 'User Stories'
        ordering = ['-prioridad_final']
    def __str__(self):
        return self.nombre_us

class SprintColaborador(models.Model):
    """Almacena todos los colaboradores"""
    colaborador = models.ForeignKey('Usuario',on_delete=models.CASCADE)
    horas = models.IntegerField(default=0)
    horasDisponibles = models.IntegerField(default=0)
        

class SprintUserStory(models.Model):
    """Almacena todos los colaboradores"""
    colaborador = models.ForeignKey('Usuario',on_delete=models.CASCADE)
    us = models.ForeignKey('UserStory',on_delete=models.CASCADE)

class Sprint(models.Model):
    """Modelo de la tabla sprint, en la cual se almacenan todos los datos del sprint"""
    proyecto_sp = models.ForeignKey('Proyecto',on_delete=models.CASCADE,null=True)
    nombre_sp = models.CharField(max_length=50,null=False)
    descripcion_sp = models.CharField(max_length=50,null=False)
    fechaIni_sp = models.DateField(null=True)
    fechaFIn_sp = models.DateField(null=True)
    userStory_sp = models.ManyToManyField('SprintUserStory',blank=True)
    estado = models.ForeignKey('Estado',on_delete=models.CASCADE)
    fecha_creacion = models.DateField(default=datetime.date.today)
    colaborador_sp = models.ManyToManyField('SprintColaborador',blank=True)
    class Meta:
        verbose_name = 'Sprint'
        verbose_name_plural = 'Sprints'
        ordering = ['estado']
    def __str__(self):
        return self.nombre_sp


Fases_CHOICES=[
    ('TODO','Por Hacer'),
    ('DOING','Haciendo'),
    ('DONE','Hecho'),
    ('CANC','Cancelado'),
]

class Fase(models.Model):
    """Modelo de la tabla Fase, en la cual se almacenan todos los datos del Fase"""
    nombre_fase = models.CharField(max_length=15)
    orden_fase = models.CharField(max_length=100,null=False)
    tipoUs = models.ForeignKey('TipoUserStory',on_delete=models.CASCADE,null=True)
    class Meta:
        verbose_name = 'Fase'
        verbose_name_plural = 'Fases'
        ordering = ['orden_fase']
    def __str__(self):
        return self.nombre_fase

    
class FaseTUS(models.Model):
    """Modelo de la tabla Fase por Tipo de User Story, en la cual se almacenan todos los datos de Fase por Tipo de Usuario"""
    #sprint_fase = models.ForeignKey(Sprint,on_delete=models.CASCADE,null=True)
    tipo_us_faseTUS = models.ForeignKey('TipoUserStory',on_delete=models.CASCADE,null=True)
    fase_faseTUS = models.ForeignKey('Fase',on_delete=models.CASCADE,null=True)
    #userStory_fase = models.ForeignKey('UserStory',on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Fase'
        verbose_name_plural = 'Fases'
    def _str_(self):
        return self.nombre_fase


class Tablero(models.Model):
    """Modelo de la tabla Tablero, en la cual se almacenan todos los datos del Tablero"""
    sprint_tablero = models.ForeignKey('Sprint',on_delete=models.CASCADE,null=True)
    tipo_us_fase = models.ForeignKey('TipoUserStory',on_delete=models.CASCADE,null=True)
    faseTUS_tablero = models.ManyToManyField('FaseTUS')
    nombre_tablero = models.CharField(max_length=50,null=False)
    fecha_creacion = models.DateField(default=datetime.date.today)
    #descripcion_tablero = models.CharField(max_length=100,null=False)
    def _str_(self):
        return self.nombre_fase

class PrioridadTUs(models.Model):
    """Listado de prioridades de los tipo de US"""
    descripcion = models.CharField(max_length=50,null=False)
    valor = models.IntegerField(null=False)
    color = models.CharField(max_length=50,null=False,default='')
    class Meta:
        verbose_name = 'PrioridadTUs'
        verbose_name_plural = 'PrioridadTUs'
        ordering = ['valor']
    def __str__(self):
        return self.descripcion

class Comentario(models.Model):
    """
    Comentarios de los userStory
    """
    comentario = models.CharField(max_length=1000,null=False)
    fecha_creacion = models.DateField(default=datetime.date.today)
    horas = models.IntegerField(null=True);
    class Meta:
        verbose_name = 'comenario'
        verbose_name_plural = 'comentarios'
        ordering = ['fecha_creacion']
    def __str__(self):
        return self.comentario

class Historial(models.Model):
    """Se almacena el historial de todo el ciclo del proyecto"""
    descripcion = models.CharField(max_length=1000,null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('Usuario',on_delete=models.CASCADE,null=True)
    class Meta:
        verbose_name = 'historial'
        verbose_name_plural = 'historiales'
        ordering = ['fecha_creacion']
    def __str__(self):
        return self.descripcion


class HoraTrabajada(models.Model):
    """Se almacena el historial de todo el ciclo del proyecto"""
    sprint = models.ForeignKey('Sprint',on_delete=models.CASCADE,null=True)
    horas = models.IntegerField()
    us = models.ForeignKey('UserStory',on_delete=models.CASCADE)
    usuario = models.ForeignKey('Usuario',on_delete=models.CASCADE,null=True)
    proyecto = models.ForeignKey('Proyecto',on_delete=models.CASCADE,null=True)
    fecha_creacion = models.DateField(default=datetime.date.today)
    class Meta:
        ordering = ['fecha_creacion']

    
