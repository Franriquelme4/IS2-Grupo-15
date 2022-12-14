import datetime
import json
from django.http import JsonResponse
from django.core import serializers
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from usuario.utils import validarPermisos,enviarNotificacion, render_to_pdf,busy_end_date,agregarHistorial, getRolByproyectUsuario,getUsuarioSesion, getTipoUsBySprint, getIdScrumRol, getProyectsByUsuarioID, getProyectsByID, getRolByProyectId, getColaboratorsByProyect, calcularFechaFin, getTipoUsbyProyectId, getTipoUsbyNotProyectId, getPermisos
from usuario.models import Usuario, FaseTUS,HoraTrabajada, TipoUs_Proyecto,Comentario, SprintUserStory, SprintColaborador, Sprint, Cliente, Proyecto, MiembroEquipo, Permiso, Rol, ProyectoRol, TipoUserStory, PrioridadTUs, UserStory, Fase, Estado
from django.template import loader
from django.db.models import Q
from datetime import datetime,timedelta
from django.views.generic import ListView,View
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO

# Create your views here.


def login(request):
    """
    Metodo de redireccion del login para poder ingresar mediante sso
    """
    return render(request, 'accounts/login.html')


@login_required(login_url="/login/")
def index(request):
    """
    Luego de loguease se lleva a la vista principal la cual tiene
    distintas opciones dependiendo el rol que tenga 
    """
    data = request.user
    usuario = Usuario.objects.filter(email=data.email)
    es_usuario_nuevo = False
    print(data.username)
    if not usuario:
        es_usuario_nuevo = True
        nuevo_usuario = Usuario(
            nombre=data.first_name,
            apellido=data.last_name,
            email=data.email,
            nombre_usuario=data.username
        )
        nuevo_usuario.save()
        userSession = nuevo_usuario
    else:
        userSession = usuario[0]
    request.session['userSesion'] = "userSession"
    proyectos = getProyectsByUsuarioID(userSession.id)
    total_proyectos = Proyecto.objects.count()
    total_usuarios = Usuario.objects.count()
    context = {
        'segment': 'index',
        'userSession': userSession,
        'proyectos': proyectos,
        'total_proyectos': total_proyectos,
        'total_usuarios': total_usuarios
    }
    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


def usuarios(request):
    """
    Se lista los usuarios actuales del sistema, este metodo se utiliza en el usuario admin
    """
    userSession = getUsuarioSesion(request.user.email)
    usuarios = Usuario.objects.all()
    rolUsuario = Rol.objects.get(id=userSession.df_rol.id)
    permisosProyecto = ['act_Usuario', 'dct_Usuario']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id)
    context = {'usuarios': usuarios,
               'segment': 'usuarios',
               'userSession': userSession,
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos}
    html_template = loader.get_template('home/usuarios.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def proyectos(request):
    """
    Se lista los proyectos actuales del sistema, este metodo se utiliza en el usuario admin
    """
    userSession = getUsuarioSesion(request.user.email)
    rolUsuario = Rol.objects.get(id=userSession.df_rol.id)
    proyectos = Proyecto.objects.all()
    permisosProyecto = ['crt_Proyecto', 'asg_Proyecto']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id)
    context = {'userSession': userSession,
               'proyectos': proyectos,
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos}
    html_template = loader.get_template('home/proyectos.html')
    return HttpResponse(html_template.render(context, request))


def GestionProyecto(request):
    usuarios = Usuario.objects.all()
    userSession = getUsuarioSesion(request.user.email)
    context = {'usuarios': usuarios,
               'segment': 'GestionProyecto', 'userSession': userSession}
    html_template = loader.get_template('home/GestionProyecto.html')
    return HttpResponse(html_template.render(context, request))


def GestionProyectoAgregar(request):
    print(request.POST['nombreProyecto'])
    variables = request.POST
    if request.method == 'POST':
        cliente = Cliente(
            nombre_cliente=variables['nombreCliente'],
            apellido_cliente=variables['apellidoCliente'],
            email_cliente=variables['emailCliente'],
            telefono_cliente=variables['telefonoCliente'],
            empresa_cliente=variables['empresaCliente']
        )
        cliente.save()
        miembro = MiembroEquipo(
            descripcion=''
        )
        miembro.save()
        miembro.miembro_rol.add(getIdScrumRol())
        miembro.miembro_usuario.add(
            Usuario.objects.get(id=variables['scrumMaster']))
        proyecto = Proyecto(
            nombre_proyecto=variables['nombreProyecto'],
            cliente_proyecto=cliente,
            descripcion_proyecto=variables['descripcion'],
            sprint_dias=variables['sprintDias']
        )
        proyecto.save()
        proyecto.miembro_proyecto.add(miembro)
        descripcion = "Se crea el proyecto"
        agregarHistorial(request,proyecto.id,descripcion)
    return redirect('/')


@login_required(login_url="/login/")
def CrearProyecto(request):
    """
    Redirige a la vista de creacion de proyectos, consiste en un formulario
    """
    usuarios = Usuario.objects.all()
    userSession = getUsuarioSesion(request.user.email)
    rolUsuario = Rol.objects.get(id=userSession.df_rol.id)
    print(rolUsuario.permiso.all())
    context = {'usuarios': usuarios,
               'segment': 'crearProyecto',
               'userSession': userSession,
               'rolUsuario': rolUsuario
               }
    html_template = loader.get_template('home/CrearProyecto.html')
    return HttpResponse(html_template.render(context, request))


def activarUsuario(request, id):
    """
    Cuando un usuario nuevo se loguea en el sistema queda en estado pendiente hasta que el admin le de acceso
    """
    usuario = Usuario.objects.get(id=id)
    usuario.activo = True
    usuario.save()
    print("ANTES DE LA NOTIFICACION")
    enviarNotificacion(1,usuario.email,None)
    print("DESPUES DE LA NOTIFICACION")
    return redirect('/')


def crearProyectoGuardar(request):
    """
    Metodo en el se crea el proyecto, realizando todos los inserts requeridos
    """
    print(request.POST['nombreProyecto'])
    variables = request.POST
    if request.method == 'POST':
        cliente = Cliente(
            nombre_cliente=variables['nombreCliente'],
            apellido_cliente=variables['apellidoCliente'],
            email_cliente=variables['emailCliente'],
            telefono_cliente=variables['telefonoCliente'],
            empresa_cliente=variables['empresaCliente']
        )
        cliente.save()
        miembro = MiembroEquipo(
            descripcion=''
        )
        miembro.save()
        miembro.miembro_rol.add(getIdScrumRol())
        miembro.miembro_usuario.add(
            Usuario.objects.get(id=variables['scrumMaster']))
        usuario = Usuario.objects.get(id=variables['scrumMaster'])
        proyecto = Proyecto(
            nombre_proyecto=variables['nombreProyecto'],
            cliente_proyecto=cliente,
            fecha_ini_proyecto=None,
            fecha_fin_proyecto=None,
            duracion=variables['duracion'],
            estado=Estado.objects.get(descripcion="PENDIENTE"),
            descripcion_proyecto=variables['descripcion'],
            sprint_dias=variables['sprintDias']
        )
        proyecto.save()
        proyecto.miembro_proyecto.add(miembro)
        descripcion = "Se crea el proyecto"
        agregarHistorial(request,proyecto.id,descripcion)
        enviarNotificacion(2,usuario.email,proyecto.nombre_proyecto)
    return redirect('/')


@login_required(login_url="/login/")
def verProyecto(request, id):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(request.user.email,'Correeo')
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs',
                        'dsp_ProductBack', 'dsp_SprinBack', 'ini_Proyecto', 'upd_Proyecto','cerrar_proyecto']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos
               }
    #descripcion = "Se ingreso al proyecto"
    #agregarHistorial(request,proyecto.id,descripcion)
    html_template = loader.get_template('home/vistaProyectos.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def rolesProyecto(request, id):
    """
    Se lista todos los roles especificos de cada proyecto
    """
    userSession = getUsuarioSesion(request.user.email)
    rolesProyecto = getRolByProyectId(id)
    permisos = Permiso.objects.all()
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(request.session['userSesion'])
    print(request.user,'Correeo')
    permisosProyecto = ['crt_rol', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack', 'dlt_rol', 'upd_rol']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'rolesProyecto',
               'permisos': permisos,
               'rolesProyecto': rolesProyecto,
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos
               }
    html_template = loader.get_template('home/rolesProyecto.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def rolesProyectoCrear(request, id):
    """
    Se lista todos los roles especificos de cada proyecto
    """
    userSession = getUsuarioSesion(request.user.email)
    rolesProyecto = getRolByProyectId(id)
    permisos = Permiso.objects.all()
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(request.session['userSesion'])
    permisosProyecto = ['crt_rol', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'rolesProyecto',
               'permisos': permisos,
               'rolesProyecto': rolesProyecto,
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos
               }
    html_template = loader.get_template('home/rolesProyectoCrear.html')
    return HttpResponse(html_template.render(context, request))



@login_required(login_url="/login/")
def colaboradoresProyecto(request, id):
    """
    Se lista todos colaboradores del proyecto
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(getPermisos(userSession.id, id), 'Permisos')
    rolesProyecto = getRolByProyectId(id)
    colaboradores = getColaboratorsByProyect(id)
    usuarios = Usuario.objects.filter(
        ~Q(id=userSession.id)).filter(~Q(df_rol=1))
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs',
                        'dsp_ProductBack', 'dsp_SprinBack', 'dlt_Colaborador', 'upd_Colaborador']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'colaboradores': colaboradores,
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'usuarios': usuarios,
        'validacionPermisos': validacionPermisos
    }
    html_template = loader.get_template('home/colaboradoresProyecto.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def colaboradoresProyectoCrear(request, id):
    """
    Se lista todos colaboradores del proyecto
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(rolUsuario.permiso.all())
    rolesProyecto = getRolByProyectId(id)
    colaboradores = getColaboratorsByProyect(id)
    usuarios = Usuario.objects.filter(
        ~Q(id=userSession.id)).filter(~Q(df_rol=1))
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador',
                        'dsp_Roles', 'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'colaboradores': colaboradores,
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'usuarios': usuarios,
        'validacionPermisos': validacionPermisos
    }
    html_template = loader.get_template('home/colaboradoresProyectoCrear.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def colaboradoresProyectoEditar(request, idProyecto, idColaborador):
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    rolesProyecto = getRolByProyectId(idProyecto)
    rolesSelect = []
    rolesNoSelect = []
    miembroEquipo = getRolByproyectUsuario(idProyecto,idColaborador)[0]
    for me in rolesProyecto:
        flag = False
        for rp in  miembroEquipo.roles:
            if rp == me.id_rol: 
                flag=True
                break
        if flag:
            rolesSelect.append(me)
        else:
           
            rolesNoSelect.append(me)   
    usuarios = Usuario.objects.filter(
        ~Q(id=userSession.id)).filter(~Q(df_rol=1))
    colaboradores = Usuario.objects.get(id=idColaborador)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador',
                        'dsp_Roles', 'dsp_TipoUs', 'dsp_ProductBack']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {
        'colaboradores': colaboradores,
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': Proyecto.objects.get(id=idProyecto),
        'rolUsuario': rolUsuario,
        'usuarios': usuarios,
        'validacionPermisos': validacionPermisos,
        'rolesSelect':rolesSelect,
        'rolesNoSelect':rolesNoSelect
    }
    html_template = loader.get_template(
        'home/colaboradoresProyectoEditar.html')
    return HttpResponse(html_template.render(context, request))

def rolesProyectoEditar(request, idProyecto, idRol):
    """
    Se lista todos los roles especificos de cada proyecto
    """
    print(f"IDROL DE ROLESPROYECTOEDITAR = {idRol}")
    print(f"IDproyecto DE ROLESPROYECTOEDITAR = {idProyecto }")
    userSession = getUsuarioSesion(request.user.email)
    permisos = Permiso.objects.all()
    print(f"PERMISOS = {permisos }")
    rolesProyecto = getRolByProyectId(idProyecto)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    rolEditar = Rol.objects.get(id=idRol)
    print(userSession.id)
    permisosSelect = Rol.objects.get(id=idRol).permiso.all()
    print(permisosSelect, 'hola')
    permisosaux = None
    for i in permisosSelect:
        permisos = permisos.filter(~Q(id=i.id))
    print(request.session['userSesion'])
    permisosProyecto = ['crt_rol', 'dsp_Colaborador',
                        'dsp_Roles', 'dsp_TipoUs', 'dsp_ProductBack']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'rolesProyecto': rolesProyecto,
               'permisos': permisos,
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'rolEditar': rolEditar,
               'permisosSelect': permisosSelect
               }
    html_template = loader.get_template('home/rolesProyectoEditar.html')
    return HttpResponse(html_template.render(context, request))

def eliminarColaboradorProyecto2(request,idColaborador,idProyecto,editar):
    variables = request.POST
    print(f"ID COLABORADOR ELIMINAR = {idColaborador}")
    usuario = Usuario.objects.get(id = idColaborador)
    record = MiembroEquipo.objects.filter(miembro_usuario=idColaborador)
    if not editar:
        descripcion = f"Se elimino colaborador: {usuario.nombre}"
        agregarHistorial(request,idProyecto,descripcion)
    record.delete()
    return redirect(f'/proyecto/{idProyecto}')


@login_required(login_url="/login/")
def eliminarRolProyecto(request, id):
    """Se elimina el rol asociado al id"""
    variables = request.POST
    record = Rol.objects.filter(id = variables.get('idRol',False))
    rol = Rol.objects.get(id = variables.get('idRol',False))
    descripcion = f"Se elimino rol del proyecto: {rol.nombre_rol}"
    agregarHistorial(request,id,descripcion)
    for x in record:
        x.permiso.clear()
    record.delete()
    return redirect(f'/proyecto/roles/{id}')


def editarRolProyecto(request, id):
    variables = request.POST
    if request.method == 'POST':
        record = Rol.objects.filter(id = variables.get('idRol',False))
        for x in record:
            x.permiso.clear()
        actualizarRolProyecto(request, id)
    return redirect(f'/proyecto/roles/{id}')


@login_required(login_url="/login/")
def actualizarRolProyecto(request, id):
    """Se crea un nuevo rol con todos los permisos asociados"""
    variables = request.POST
    if request.method == 'POST':
        idRol = variables.get('idRol', False)
        rol = Rol.objects.get(id=idRol)
        Rol.objects.filter(id=idRol).update(
            descripcion_rol=variables.get('descripcion', False),
            nombre_rol=variables.get('nombre_rol', False),
        )
        for permiso in variables.getlist('permisos', False):
            print(permiso)
            rol.permiso.add(Permiso.objects.get(id=permiso))
        descripcion = f"Se actualizo los permisos del rol: {rol.nombre_rol}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/roles/{id}')


@login_required(login_url="/login/")
def crearRolProyecto(request, id):
    """Se crea un nuevo rol con todos los permisos asociados"""
    variables = request.POST
    if request.method == 'POST':
        rol = Rol(
            descripcion_rol=variables.get('descripcion', False),
            nombre_rol=variables.get('nombre_rol', False),
        )
        rol.save()
        for permiso in variables.getlist('permisos', False):
            print(Permiso.objects.get(id=permiso))
            rol.permiso.add(Permiso.objects.get(id=permiso))
        proyecto_rol = ProyectoRol(
            descripcion_proyecto_rol=''
        )
        proyecto_rol.save()
        proyecto_rol.rol.add(rol)
        proyecto_rol.proyecto.add(Proyecto.objects.get(id=id))
        descripcion = f"Se creo nuevo rol: {rol.nombre_rol}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/roles/{id}')

def editarColaboradorProyecto(request, idProyecto):
    """Se eliminan los colaboradores de un proyecto especifico"""
    variables = request.POST
    if request.method == 'POST':
        idColaborador = variables.get('idColaborador', False)
        print(f"ID COLABORADOR EDITAR = {idColaborador}")
        print(f"ID PROYECTO EDITAR= {idProyecto}")
        editar = True
        eliminarColaboradorProyecto2(request, idColaborador, idProyecto,editar)
        asignarColaboradorProyecto(request, idProyecto,editar)

        usuario = Usuario.objects.get(id = idColaborador)
        descripcion = f"Se edito el colaborador: {usuario.nombre}"
        agregarHistorial(request,idProyecto,descripcion)

    return redirect(f'/proyecto/colaboradores/{idProyecto}')

@login_required
def asignarColaboradorProyecto(request, id, editar):
    """Se almacena el nuevo rol con el colaborador al proyecto"""
    print(f"editar:{editar}")
    variables = request.POST
    roles = variables.getlist('rol', False)
    if request.method == 'POST':
        miembro = MiembroEquipo(
            descripcion=''
        )
        miembro.save()
        for rol in variables.getlist('rol', False):
            print(rol, 'rol')
            miembro.miembro_rol.add(Rol.objects.get(id=rol))
        usuario = Usuario.objects.get(id=variables.get('usuario', False))
        miembro.miembro_usuario.add(usuario)
        proyecto = Proyecto.objects.get(id=id)
        proyecto.miembro_proyecto.add(miembro)
        if not editar:
            descripcion = f"Se asigno nuevo colaborador: {usuario.nombre}"
            agregarHistorial(request,id,descripcion)
        enviarNotificacion(3,usuario.email,proyecto.nombre_proyecto)
    return redirect(f'/proyecto/colaboradores/{id}')


@login_required
def eliminarColaboradorProyecto(request, id):
    variables = request.POST
    print("ID COLABORADOR 576")
    print(variables.get('idColaborador',False))
    record = MiembroEquipo.objects.filter(miembro_usuario = variables.get('idColaborador',False))
    usuario = Usuario.objects.get(id = variables.get('idColaborador',False))
    descripcion = f"Se elimino colaborador: {usuario.nombre}"
    agregarHistorial(request,id,descripcion)
    record.delete()
    return redirect(f'/proyecto/colaboradores/{id}')


@login_required
def tipoUs(request, id):
    """Se listan todos los tipos de US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print('view: ', id)
    tipoUs = getTipoUsbyProyectId(id)
    #prioridad = PrioridadTUs.objects.all()
    rolesProyecto = getRolByProyectId(id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs',
                        'dsp_ProductBack', 'ctr_TipoUs', 'imp_TipoUs', 'dsp_SprinBack', 'dlt_TipoUs', 'upd_TipoUs']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'prueba': rolesProyecto,
        'tipoUs': tipoUs,
        # 'prioridades':prioridad,
    }
    html_template = loader.get_template('home/tipoUS.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def tipoUsCrear(request, id):
    """Se listan todos los tipos de US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    prioridad = PrioridadTUs.objects.all()
    print(tipoUs)
    rolesProyecto = getRolByProyectId(id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'ctr_TipoUs', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'prueba': rolesProyecto,
        'prioridades': prioridad
    }
    html_template = loader.get_template('home/tipoUSCrear.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def crearTUSProyecto(request, id):
    """Se almacena en base de datos el nuevo tipo de US"""
    variables = request.POST
    if request.method == 'POST':
        jsonFase = json.loads(variables.get('jsonFase', False))
        tipoUs = TipoUserStory(
            nombre_tipo_us=variables.get('nombre', False),
            descripcion_tipo_us=variables.get('descripcion', False),
            proyecto_tipo_us = Proyecto.objects.get(id=id)

        )
        tipoUs.save()
        print(jsonFase)
        for faseJson in jsonFase:
            Fase.objects.create(
                nombre_fase=faseJson['nombre'],
                orden_fase=faseJson['orden'],
                tipoUs=tipoUs
            )
        TipoUs_Proyecto.objects.create(
            proyecto=Proyecto.objects.get(id=id),
            tipoUs=tipoUs
        )
        descripcion = f"Se creo nuevo tipo de US: {tipoUs.nombre_tipo_us}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/tipoUs/{id}')


@login_required
def tipoUsImportar(request, id):
    """Se listan todos los tipos de US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    prioridad = PrioridadTUs.objects.all()
    tipoUs = getTipoUsbyProyectId(id)
    todostipoUs = getTipoUsbyNotProyectId(id)
    print(tipoUs)
    rolesProyecto = getRolByProyectId(id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'ctr_TipoUs', 'dsp_SprinBack', 'imp_TipoUs']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'prueba': rolesProyecto,
        'todostipoUs': todostipoUs,
        'prioridades': prioridad
    }
    html_template = loader.get_template('home/tipoUSImportar.html')
    return HttpResponse(html_template.render(context, request))


def importarTusDeProyecto(request, id):
    variables = request.POST
    print("idTipoUs")
    if request.method == 'POST':
        tipoUs = TipoUserStory.objects.get(id=variables.get('idTipoUs', False))
        idproyO = TipoUserStory.objects.get(id=variables.get('idTipoUs', False)).proyecto_tipo_us_id
        proyectoO = Proyecto.objects.get(id = idproyO)
        proyecto = Proyecto.objects.get(id=id)
        TipoUs_Proyecto.objects.create(proyecto=proyecto, tipoUs=tipoUs)

        descripcion = f"Se importo tipos de US: {tipoUs.nombre_tipo_us} del proyecto {proyectoO.nombre_proyecto}"
        agregarHistorial(request,id,descripcion)   
    return redirect(f'/proyecto/tipoUs/{id}')


@login_required
def verProductBacklog(request, id):
    """Se visualiza todos los US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    rolesProyecto = getRolByProyectId(id)
    # tipoUs = TipoUserStory.objects.filter(proyecto_tipo_us = id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'crt_US', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    userStorys = UserStory.objects.filter(proyecto_us=id)
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'tipoUs': tipoUs,
        'prueba': rolesProyecto,
        'userStorys': userStorys
    }
    html_template = loader.get_template('home/productBacklog.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def crearUs(request, id):
    """Se listan todos los tipos de US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    prioridad = PrioridadTUs.objects.all()
    tipoUs = TipoUs_Proyecto.objects.filter(proyecto=id)
    print(tipoUs)
    rolesProyecto = getRolByProyectId(id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'ctr_TipoUs', 'crt_US', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'prueba': rolesProyecto,
        'prioridades': prioridad,
        'tipoUs': tipoUs,
    }
    html_template = loader.get_template('home/usCrear.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def crearUsGuardar(request, id):
    """Se agregan los nuevos Us"""
    variables = request.POST
    if request.method == 'POST':
        pn = float(variables.get('prioridad-negocio', False))
        pt = float(variables.get('prioridad-tecnica', False))
        userStory = UserStory(
            proyecto_us=Proyecto.objects.get(id=id),
            nombre_us=variables.get('nombre', False),
            descripcion_us=variables.get('descripcion', False),
            tiempoEstimado_us=variables.get('tiempo', False),
            tipo_us=TipoUserStory.objects.get(
                id=variables.get('tipoUs', False)),
            prioridad_negocio=pn,
            prioridad_tecnica=pt,
            prioridad_final=round((0.6*pn+0.4*pt)+0)
        )
        userStory.save()
        descripcion = f"Creacion de UserStory nombre: {userStory.nombre_us}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/productBacklog/{id}')

@login_required
def editarProyecto(request, id):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(getPermisos(userSession.id, id), 'Permisos')
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos
               }
    html_template = loader.get_template('home/editarProyecto.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def editarProyectoGuardar(request, id):
    """
    Metodo en el se crea el proyecto, realizando todos los inserts requeridos
    """
    print(request.POST['nombreProyecto'])
    variables = request.POST
    if request.method == 'POST':
        Cliente.objects.filter(id=variables['idCliente']).update(
            nombre_cliente=variables['nombreCliente'],
            apellido_cliente=variables['apellidoCliente'],
            email_cliente=variables['emailCliente'],
            telefono_cliente=variables['telefonoCliente'],
            empresa_cliente=variables['empresaCliente']
        )
        Proyecto.objects.filter(id=id).update(
            nombre_proyecto=variables['nombreProyecto'],
            duracion=variables['duracion'],
            descripcion_proyecto=variables['descripcion'],
            sprint_dias=variables['sprintDias']
        )
        descripcion = f"Se edito el proyecto"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/{id}')


@login_required
def iniciarProyecto(request, id):
    proyectoActual = Proyecto.objects.get(id=id)
    Proyecto.objects.filter(id=id).update(
        fecha_ini_proyecto=datetime.today(),
        fecha_fin_proyecto=calcularFechaFin(
            datetime.today(), proyectoActual.duracion),
        estado=Estado.objects.get(descripcion="EN PROGRESO"),
    )
    descripcion = f"Se inicio el proyecto"
    agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/{id}')


@login_required
def sprintProyecto(request, id):
    """Se visualiza todos los US"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    rolesProyecto = getRolByProyectId(id)
    sprint = Sprint.objects.filter(proyecto_sp=id).order_by("-estado")
    print(sprint, 'sprint')
    # tipoUs = TipoUserStory.objects.filter(proyecto_tipo_us = id)
    permisosProyecto = ['agr_Colaborador', 'dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs', 'dsp_ProductBack','dsp_Velocity','dsp_Burndown',
                        'crt_Sprint', 'dsp_SprinBack', 'dsp_Colaborador_Sprint', 'dsp_SprinBack', 'dsp_Tablero', 'agr_Colaborador_US','ini_sprint','cancelar_sprint']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    userStorys = UserStory.objects.filter(proyecto_us=id)
    print(proyecto.sprint_actual,"saprint ")
    context = {
        'rolesProyecto': rolesProyecto,
        'userSession': userSession,
        'proyecto': proyecto,
        'rolUsuario': rolUsuario,
        'validacionPermisos': validacionPermisos,
        'tipoUs': tipoUs,
        'prueba': rolesProyecto,
        'userStorys': userStorys,
        'sprint': sprint
    }
    html_template = loader.get_template('home/sprint.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def sprintCrear(request, id):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    userStorys = UserStory.objects.filter(proyecto_us=id)
    colaboradores = getColaboratorsByProyect(id)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack', 'ctr_Sprint']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'userStorys': userStorys,
               'colaboradores': colaboradores
               }
    html_template = loader.get_template('home/sprintCrear.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def sprintCrearGuardar(request, id):
    """Se guardan los datos iniciales del sprint"""
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    variables = request.POST
    #print(variables.get('fecha_inicio',False),proyecto.sprint_dias)
    #print(str(busy_end_date(datetime. strptime(variables.get('fecha_inicio',False),'%Y-%m-%d'),proyecto.sprint_dias)))
    if request.method == 'POST':
        sprint = Sprint.objects.create(
            descripcion_sp=variables.get('descripcion', False),
            nombre_sp=variables.get('nombre', False),
            # fechaIni_sp=variables.get('fecha_inicio', False),
            # fechaFIn_sp=busy_end_date(datetime. strptime(variables.get(
            #     'fecha_inicio', False), '%Y-%m-%d'), proyecto.sprint_dias),
            proyecto_sp=Proyecto.objects.get(id=id),
            estado=Estado.objects.get(descripcion="PENDIENTE"),
        )
        sprint.save()
        descripcion = f"Creacion de Sprint nombre = {sprint.nombre_sp}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/sprint/{id}')

@login_required
def sprintColaboradores(request, idProyecto, idSprint):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    aux = Sprint.objects.get(id=idSprint).colaborador_sp.all()
    for i in aux:
        print(i.colaborador, 'col')
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    colaboradores = Sprint.objects.get(id=idSprint).colaborador_sp.all()
    print(colaboradores)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs',
                        'dsp_ProductBack', 'dsp_SprinBack', 'agr_Colaborador', 'agr_Colaborador_US']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'colaboradores': colaboradores,
               'sprint': Sprint.objects.get(id=idSprint)
               }
    html_template = loader.get_template('home/sprintColaboradores.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def sprintColaboradorAgregar(request, idProyecto, idSprint):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    colaboradoresSprint = Sprint.objects.get(id=idSprint).colaborador_sp.all()
    colaboradoresProyecto = getColaboratorsByProyect(idProyecto)
    colaboradores = []
    for cP in colaboradoresProyecto:
        flag = True
        for cSp in colaboradoresSprint:
            print(cSp.colaborador.nombre, cP.nombre)
            if cP.id == cSp.colaborador.id:
                flag = False
        if flag:
            colaboradores.append(cP)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles', 'dsp_TipoUs',
                        'dsp_ProductBack', 'dsp_SprinBack', 'agr_Colaborador_US']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'colaboradores': colaboradores,
               'sprint': Sprint.objects.get(id=idSprint)
               }
    html_template = loader.get_template('home/sprintAgregarColaborador.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def sprintColaboradorAgregarGuardar(request, id):
    """Se almacenan los colaboradores del Sprint"""
    userSession = getUsuarioSesion(request.user.email)
    variables = request.POST
    proyecto = getProyectsByID(id, userSession.id)[0]
    if request.method == 'POST':
        sprint = Sprint.objects.get(id=variables.get('idSprint', False))
        usuario = Usuario.objects.get(id=variables.get('usuario', False))
        spColaborador = SprintColaborador.objects.create(
            colaborador= usuario,
            horas=variables.get('horas', False),
            horasDisponibles=int(variables.get(
                'horas', False))*proyecto.sprint_dias
        )
        sprint.colaborador_sp.add(spColaborador)
        descripcion = f"Colaborador : {usuario.nombre} anhadido al Sprint: {sprint.nombre_sp}"
        agregarHistorial(request,id,descripcion)
    return redirect(f'/proyecto/sprint/{id}')

@login_required
def sprintUsAgregar(request, idProyecto, idSprint):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    aux = Sprint.objects.get(id=idSprint).userStory_sp.all()
    for i in aux:
        print(i.us, 'col')
    userStorys = UserStory.objects.filter(
        proyecto_us=idProyecto, disponible=True)
    colaboradores = Sprint.objects.get(
        id=idSprint).colaborador_sp.filter(horasDisponibles__gte=0)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'colaboradores': colaboradores,
               'sprint': Sprint.objects.get(id=idSprint),
               'userStorys': userStorys
               }
    html_template = loader.get_template('home/sprintAgregarUs.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def sprintUsAgregarGuardar(request, id):
    """Se almacenan los colaboradores del Sprint"""
    variables = request.POST
    if request.method == 'POST':
        sprint = Sprint.objects.get(id=variables.get('idSprint', False))
        spUs = SprintUserStory.objects.create(
            colaborador=Usuario.objects.get(
                id=variables.get('colaborador', False)),
            us=UserStory.objects.get(id=variables.get('us', False)),
        )
        sColaboradorGet = sprint.colaborador_sp.get(
            colaborador=int(variables.get('colaborador', False)))
        sColaborador = sprint.colaborador_sp.filter(
            colaborador=int(variables.get('colaborador', False)))
        sColaborador.update(horasDisponibles=sColaboradorGet.horasDisponibles -
                            UserStory.objects.get(id=variables.get('us', False)).tiempoEstimado_us)
        TipoUsEditar = UserStory.objects.get(
            id=variables.get('us', False)).tipo_us
        userStory = UserStory.objects.get(id=variables.get('us', False))
        UserStory.objects.filter(id=variables.get('us', False)).update(
            disponible=False, fase=Fase.objects.get(tipoUs=TipoUsEditar, orden_fase=1),
            prioridad_sprint=userStory.prioridad_sprint+3,
            prioridad_final=round((0.6*userStory.prioridad_negocio+0.4 *
                                  userStory.prioridad_tecnica)+userStory.prioridad_sprint+3)
        )
        sprint.userStory_sp.add(spUs)
        
        descripcion = f"US: {userStory.nombre_us} anhadido al Sprint: {sprint.nombre_sp}"
        agregarHistorial(request,id,descripcion)

    return redirect(f'/proyecto/sprint/{id}')

@login_required
def sprintBacklog(request, idProyecto, idSprint):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    userStorys = Sprint.objects.get(id=idSprint).userStory_sp.all()
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack','reasignar_us']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'sprint': Sprint.objects.get(id=idSprint),
               'userStorys': userStorys
               }
    html_template = loader.get_template('home/sprintBackLog.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def sprintTablero(request, idProyecto, idSprint, idTipoUs=None):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    userStorys = Sprint.objects.get(id=idSprint).userStory_sp.all()
    tipoUs = getTipoUsBySprint(userStorys)
    tipoUsTablero = ''
    if idTipoUs or idTipoUs == 0:
        if idTipoUs == 0:
            tipoUsTablero = tipoUs[0]
        else:
            tipoUsTablero = TipoUserStory.objects.get(id=idTipoUs)
    else:
        variables = request.POST
        if request.method == 'POST':
            idTp = json.loads(variables.get('tipoUsId', False))
            tipoUsTablero = TipoUserStory.objects.get(id=idTp)
    fases = Fase.objects.filter(tipoUs=tipoUsTablero)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack','fin_us']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'sprint': Sprint.objects.get(id=idSprint),
               'userStorys': userStorys,
               'tipoUs': tipoUs,
               'tipoUsTablero': tipoUsTablero,
               'fases': fases
               }
    html_template = loader.get_template('home/sprintTablero.html')
    return HttpResponse(html_template.render(context, request))


def pruebaAjax(request):
    print('llegue')
    return redirect(f'/proyecto/sprint/2')


@login_required
def sprintTableroActualizarEstado(request, idProyecto, idSprint):
    """Se actualiza el estado de us una vez que se desliza y se suelta en el estado en el cual se quiere dejar"""
    variables = request.POST
    if request.method == 'POST':
        idUserStory = variables.get('userStory', False)
        idNuevaFase = variables.get('nuevaFase', False)
        idTipoUs = variables.get('tipoUsId', False)
        UserStory.objects.filter(id=idUserStory).update(
            fase=Fase.objects.get(id=idNuevaFase)
        )
        US = UserStory.objects.get(id=idUserStory)
        sp = Sprint.objects.get(id=idSprint)
        fas = Fase.objects.get(id=idNuevaFase)
    descripcion = f"Se actualizo a fase: {fas.nombre_fase} al US: {US.nombre_us} del Sprint: {sp.nombre_sp}"
    agregarHistorial(request,idProyecto,descripcion)

    return redirect(f'/proyecto/sprint/tablero/{idProyecto}/{idSprint}/{idTipoUs}')

@login_required
def verDetallesUs(request, idProyecto, idUs):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    userStory = UserStory.objects.get(id=idUs)

    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'userStory': userStory,
               'tipoUs': tipoUs,
               }
    html_template = loader.get_template('home/usDetalle.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def getComentarios(request):
    """Se optienen todos los comentarios de un user Story"""
    if request.accepts and request.method == "GET":
        idUs = request.GET.get("idUs", None)
        userStory = UserStory.objects.get(id=idUs)
        comentario = userStory.comentario.all()
        return JsonResponse(
            {"valid":True,
            "comentario":serializers.serialize('json', comentario),
            "userStory":serializers.serialize('json', [userStory,])
            }
            , status = 200)
    return JsonResponse({}, status = 400)  

@login_required
def guardarComentarioUs(request, idProyecto, idSprint):
    """Cada us tiene la posibilidad de tener comentarios, dicho metodo se utiliza para almacenar la misma"""
    variables = request.POST
    if request.method == 'POST':
        comentario = variables.get('comentario', False)
        horasTrabajadas = int(variables.get('horasTrabajadas', False))
        idUs = variables.get('idUs', False)
        newComentario = Comentario(
        comentario = comentario,
        horas = horasTrabajadas
       )
        newComentario.save()
        userStory = UserStory.objects.get(id=idUs)
        UserStory.objects.filter(id=idUs).update(
            tiempoTrabajado = userStory.tiempoTrabajado + horasTrabajadas
        )
        HoraTrabajada.objects.create(
           sprint =Sprint.objects.get(id=idSprint),
           horas= horasTrabajadas,
            us=UserStory.objects.get(id=idUs),
            proyecto=Proyecto.objects.get(id=idProyecto)
        ) 
        userStory.comentario.add(newComentario)
        descripcion = f"Se agrego un comentario: '{newComentario.comentario}' al US: {userStory.nombre_us}"
        agregarHistorial(request,idProyecto,descripcion)
    return redirect(f'/proyecto/sprint/tablero/{idProyecto}/{idSprint}/0')
@login_required
def iniciarSprint(request, idProyecto, idSprint):
    """Se inicia el sprint una vez que se haya cargado todos los datos, se calcula la fecha """
    sprint = Sprint.objects.filter(id = idSprint)
    sp = Sprint.objects.get(id = idSprint)
    proyectoActual = Proyecto.objects.filter(id = idProyecto)
    proyecto = Proyecto.objects.get(id = idProyecto)
    fecha_hoy = datetime.today()
    sprint.update(
        fechaIni_sp=fecha_hoy,
        fechaFIn_sp=busy_end_date(fecha_hoy, proyecto.sprint_dias),
        estado=Estado.objects.get(descripcion="EN PROGRESO")
    )
    proyectoActual.update(
       sprint_actual = sprint[0] 
    )
    descripcion = f"Se inicio el sprint: {sp.nombre_sp}"
    agregarHistorial(request,idProyecto,descripcion)
    return redirect(f'/proyecto/sprint/{idProyecto}')

@login_required
def cancelarSprint(request):
    """Se cancela el sprint, regresando la disponibilidad de los user story"""
    if request.accepts and request.method == "GET":
        idSprint = request.GET.get("idSprint", None)
        idProyecto = request.GET.get("idProyecto", None)
        sprint = Sprint.objects.filter(id = idSprint)
        sprintActual = Sprint.objects.get(id = idSprint).userStory_sp.all()
        for sp in sprintActual:
            if not sp.us.finalizado:
                UserStory.objects.filter(id = sp.us.id).update(
                    disponible = True
                )
        proyectoActual = Proyecto.objects.filter(id = idProyecto)
        proyecto = Proyecto.objects.get(id = idProyecto)
        fecha_hoy = datetime.today()
        sprint.update(
            estado=Estado.objects.get(descripcion="CANCELADO")
        )
        proyectoActual.update(
        sprint_actual = None
        )
        return JsonResponse({} , status = 200)
    return JsonResponse({}, status = 400)  

@login_required
def verDocumentacion(request):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    context = {}
    html_template = loader.get_template('home/usDetalle.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def finalizarUserStory(request,idProyecto):
    """Una vez que se encuentre en done el scrum tiene la posibilidad de leer finalizar el user story"""
    print(f"Finalizar Proyecto: {idProyecto}" )
    if request.accepts and request.method == "GET":
        idUs = request.GET.get("idUs", None)
        userStory = UserStory.objects.filter(id=idUs)
        userStory.update(finalizado = True)
        
        US = UserStory.objects.get(id=idUs)
        descripcion = f"Se finalizo el US: {US.nombre_us}"
        agregarHistorial(request,idProyecto,descripcion)

        return JsonResponse({} , status = 200)
    return JsonResponse({}, status = 400)  

@login_required
def sprintUsEditar(request,idProyecto,idSprint):
    """
    Cuando un usuario ingresa a un proyecto en el cual fue asignado se visualizan 
    todos los datos de la misma 
    """
    variables = request.POST
    if request.method == 'POST':
        us = variables.get('idUs', False)
        print(us,'datos del front')
    sprintUs = SprintUserStory.objects.get(id = us)
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    userStorys = UserStory.objects.get(id=sprintUs.us.id)
    print(userStorys,"userStory")
    colaboradores = Sprint.objects.get(id=idSprint).colaborador_sp.filter(horasDisponibles__gte=0)
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(
        permisosProyecto, userSession.id, idProyecto)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'segment': 'verProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos,
               'colaboradores': colaboradores,
               'colaboradorActual':Usuario.objects.get(id=sprintUs.colaborador.id),
               'sprint': Sprint.objects.get(id=idSprint),
               'userStory': userStorys,
               'userStoryActual':sprintUs
               }
    html_template = loader.get_template('home/sprintReasignarUs.html')
    return HttpResponse(html_template.render(context, request))

@login_required
def sprintUsEditarGuardar(request,id):
    """Se almacenan los colaboradores del Sprint"""
    variables = request.POST
    if request.method == 'POST':
        spUsget = SprintUserStory.objects.get(id =variables.get('usSprint', False))
        sprint = Sprint.objects.get(id=variables.get('idSprint', False))
        sColaboradorGet = sprint.colaborador_sp.get(colaborador=int(variables.get('colaborador', False)))
        sColaborador = sprint.colaborador_sp.filter(colaborador=int(variables.get('colaborador', False)))
        sColaborador.update(horasDisponibles=sColaboradorGet.horasDisponibles - spUsget.us.tiempoEstimado_us)

        sColaboradorGet = sprint.colaborador_sp.get(colaborador=spUsget.colaborador.id)
        sColaborador = sprint.colaborador_sp.filter(colaborador=spUsget.colaborador.id)
        sColaborador.update(horasDisponibles=sColaboradorGet.horasDisponibles + spUsget.us.tiempoEstimado_us)

        SprintUserStory.objects.filter(id = variables.get('usSprint', False) ).update(
            colaborador=Usuario.objects.get(id=variables.get('colaborador', False)),
            us=UserStory.objects.get(id=int(variables.get('us', False))),
        )
        sColaboradorGet = sprint.colaborador_sp.get(colaborador=int(variables.get('colaborador', False)))
        sColaborador = sprint.colaborador_sp.filter(colaborador=int(variables.get('colaborador', False)))
        sColaborador.update(horasDisponibles=sColaboradorGet.horasDisponibles - UserStory.objects.get(id=variables.get('us', False)).tiempoEstimado_us)
        
        descripcion = f"Se edito el sprint: {sprint.nombre_sp}"
        agregarHistorial(request,id,descripcion)

    return redirect(f'/proyecto/sprint/{id}')


@login_required
def visualizarVelocity(request,idProyecto):
    """Se visualiza el velocity chart"""
    variables = request.POST
    print("Velocity Proyecto: " + str(idProyecto))
    #if request.method == 'POST':
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto,userSession.id)[0]
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, idProyecto)
    sprint = Sprint.objects.filter(proyecto_sp = idProyecto)
    dataVelocity = []
    arraysprint = []
    arrayCUS = []
    arrayCUSF = []
    
    for sp in sprint:
        arraysprint.append(sp.nombre_sp)
        totalUs = 0
        terminados = 0
        userStory = sp.userStory_sp.all()
        for us in userStory:
            totalUs = totalUs + 1
            if us.us.finalizado == True:
                   terminados = terminados + 1
        arrayCUS.append(totalUs)
        arrayCUSF.append(terminados)
    
    arrayCUS.append(0)
    arrayCUSF.append(0)

    dataVelocity = {
    "nombre":arraysprint,
    "estimado":arrayCUS, 
    "terminado":arrayCUSF 
    }
    #print(dataVelocity)
    dicc_velocity = json.dumps(dataVelocity)
    #print(dicc_velocity)
    context={
    'userSession':userSession,
    'proyecto':proyecto,
    'validacionPermisos': validacionPermisos,
    'dicc_velocity' : dicc_velocity
    }
    html_template = loader.get_template('home/velocityChart.html')
    return HttpResponse(html_template.render(context,request))

@login_required(login_url="/login/")
def verHistorialProyecto(request, id):
    """
    Se lista todos los roles especificos de cada proyecto
    """
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(id, userSession.id)[0]
    rolUsuario = Rol.objects.get(id=proyecto.id_rol)
    print(request.session['userSesion'])
    print("Usuario nombre", request.user.first_name)
    permisosProyecto = ['crt_rol', 'dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, id)
    context = {'userSession': userSession,
               'proyecto': proyecto,
               'historial':Proyecto.objects.get(id = id).historial.all(),
               'segment': 'rolesProyecto',
               'rolUsuario': rolUsuario,
               'validacionPermisos': validacionPermisos
               }
    html_template = loader.get_template('home/historialProyecto.html')
    return HttpResponse(html_template.render(context, request))

# def ListHistorialPdf(request,id):
#     proyecto = Proyecto.objects.get(id=id)
#     data = {
#         'historial':proyecto.historial.all(),
#         'proyecto':proyecto
#     }
#     pdf = render_to_pdf('reportes/historial.html',data)
#     return HttpResponse(pdf, content_type='application/pdf')

def ListHistorialPdf(request,id):
    """Se descarga el archivo pdf del historial"""
    template_path = 'reportes/historial.html'
    proyecto = Proyecto.objects.get(id=id)
    context = {
        'historial':proyecto.historial.all(),
        'proyecto':proyecto
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historial_{proyecto}_{datetime.today()}.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def cerrarProyecto(request):
    """Se encarga de cerrar el proyecto pero da la posibilidad de aun poder ver los parametros"""
    if request.accepts and request.method == "GET":
        idProyecto = request.GET.get("idProyecto", None)
        proyecto = Proyecto.objects.filter(id=idProyecto)
        proyecto.update(
            estado=Estado.objects.get(descripcion="CANCELADO")  
        )
        sprint = Sprint.objects.all()
        for sp in sprint:
            Sprint.objects.filter(id=sp.id).update(
                estado=Estado.objects.get(descripcion="CANCELADO")
        )
        return JsonResponse({} , status = 200)
    return JsonResponse({}, status = 400)  
@login_required
def visualizarBurndown(request,idProyecto,idSprint):
    variables = request.POST
    #if request.method == 'POST':
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto,userSession.id)[0]

    cantidadUs = Sprint.objects.get(id=idSprint).userStory_sp.count
    cantidadDiasSprint = Proyecto.objects.get(id = idProyecto).duracion
    

    arrayCUS = []
    arrayCUSF = []
    userStory = Sprint.objects.get(id=idSprint).userStory_sp.all()
    for us in userStory:
        horasUs = horasUs + us.tiempoEstimado_us
    
    for us in userStory:
        horaReal = horaReal + us.tiempoTrabajado

    

    duracionSprint = Sprint.objects.get(id=idSprint)
    arrayCUS.append(totalUs)
    arrayCUSF.append(terminados)

    context={
    'userSession':userSession,
    'proyecto':proyecto,
    'cantidadUs': cantidadUs,
    'cantidadDiasSprint' : cantidadDiasSprint
    }

    html_template = loader.get_template('home/burndownchart.html')
    return HttpResponse(html_template.render(context,request))



    #return redirect(f'/proyecto/sprint/burndownchart/{idProyecto}/{idSprint}')




@login_required
def visualizarBurndown2(request,idProyecto,idSprint):
    """Se visualia el burndown chart, el cual muestra el grafico de como se esta avanzando con el proyecto, teniendo una vista ideal y el real"""
    variables = request.POST
    #if request.method == 'POST':
    userSession = getUsuarioSesion(request.user.email)
    proyecto = getProyectsByID(idProyecto,userSession.id)[0]
    permisosProyecto = ['dsp_Colaborador', 'dsp_Roles',
                        'dsp_TipoUs', 'dsp_ProductBack', 'dsp_SprinBack']
    validacionPermisos = validarPermisos(permisosProyecto, userSession.id, idProyecto)
    cantidadDiasSprint = Proyecto.objects.get(id = idProyecto).sprint_dias
    arraydias = []
    arrayIdeal = []
    arrayBurn = []
    userStory = Sprint.objects.get(id=idSprint).userStory_sp.all()
    horasUs = 0
    horaReal = 0

    for us in userStory:
        horasUs = horasUs + us.us.tiempoEstimado_us

    print(f"horasUS: {horasUs}")
    sprintActual = Sprint.objects.get(id=idSprint)
    idealxdia = round(horasUs/cantidadDiasSprint)
    arraydias.append(f"""{sprintActual.fechaIni_sp}""")

    for i in range(0,cantidadDiasSprint):
        arraydias.append(f"Dia {i + 1}")
        #Math.round(totalHoursInSprint - (idealHoursPerDay * i++) + sumArrayUpTo(scopeChange, 0))
        ideal = round(horasUs - (idealxdia * i))
        if ideal >= 0:
            arrayIdeal.append(ideal)
        else:
            break

    sprintActual = Sprint.objects.get(id=idSprint)
    fechaInicio = sprintActual.fechaIni_sp
    aux=[]
    flag=0
    arrayBurn.append(horasUs)
    while 1==1:
        horasTrabajadas=0
        aux = HoraTrabajada.objects.filter(sprint=idSprint).filter(fecha_creacion__range=(fechaInicio,fechaInicio+timedelta(days = flag)))
        print(fechaInicio+timedelta(days = flag),"aux")
        for a in aux:
            horasTrabajadas+=a.horas
        arrayBurn.append(horasUs-horasTrabajadas)
        flag+=1
        if fechaInicio+timedelta(days = flag) > datetime.date(datetime.today()):
            break
 
    # for us in userStory:
    #     horaReal = horaReal + us.us.tiempoTrabajado
    #     arrayBurn.append(horaReal)
    
    # arrayBurn = arrayBurn[::-1]

    dataBurndown = {
        "TotalDias" : cantidadDiasSprint,
        "Dias" : arraydias,
        "totalHoursInSprint" : horasUs,
        "arrayIdeal" : arrayIdeal,
        "arrayBurn" : arrayBurn
    }
    #print(dataBurndown)
    dicc_Burndown = json.dumps(dataBurndown)
    print(dicc_Burndown)


    context={
    'userSession':userSession,
    'proyecto':proyecto,
    'cantidadDiasSprint' : cantidadDiasSprint,
    'validacionPermisos': validacionPermisos,
    'dicc_Burndown' : dicc_Burndown
    }

    html_template = loader.get_template('home/burndownchart2.html')
    return HttpResponse(html_template.render(context,request))
