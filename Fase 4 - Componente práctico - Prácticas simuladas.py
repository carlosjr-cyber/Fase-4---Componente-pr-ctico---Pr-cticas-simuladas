#=============================================================================
# Universidad Nacional Abierta y a Distancia (UNAD)
# Nombre del estudiante: Carlos Alberto Córdoba Mosquera y Abraham Sanchez Palacios
# Código Fuente: autoría propia
# Curso: Programación 
# Codigo 213023A_123
# Fase 4: Componente práctico - Prácticas simuladas
# Ejercicio: SISTEMA INTEGRAL DE GESTION DE CLIENTES, SERVICIOS Y RESERVAS
#=============================================================================
# -*- coding: utf-8 -*-
"""
==============================================================================
Empresa: SOFTWARE FJ
Versión: COMPLETA (100% funcional)
==============================================================================
Requisitos cubiertos (Anexo 3 - Fase 4):
  * Programacion orientada a objetos: abstraccion, herencia, polimorfismo,
    encapsulamiento.
  * Sin uso de bases de datos: los datos se gestionan con objetos y listas
    (diccionarios) en memoria. Los archivos se usan UNICAMENTE para el log
    de eventos y errores (software_fj_logs.log).
  * Clase abstracta de entidad general (Entidad).
  * Clase Cliente con validaciones robustas y encapsulamiento.
  * Clase abstracta Servicio con 3 servicios especializados que heredan de ella
    (ReservaSalas, AlquilerEquipos, AsesoriaEspecializada) y sobrescriben
    calcular_costo(), validar_parametros() y describir() (polimorfismo).
  * Sobrecarga de metodos: en Python se implementa con parametros opcionales
    (*args/**kwargs / valores por defecto); calcular_costo admite variantes
    con impuesto y/o descuento.
  * Clase Reserva con confirmacion, cancelacion y procesamiento.
  * Manejo avanzado de excepciones: excepciones personalizadas, try/except,
    try/except/else, try/except/finally y encadenamiento (raise ... from ...).
  * Simulacion automatica de mas de 10 operaciones (validas e invalidas) que
    demuestra que el sistema sigue funcionando ante errores.
==============================================================================
"""

import sys
import math
import re
from abc import ABC, abstractmethod
from datetime import datetime


# ==============================================================================
# 1. GESTOR DE LOGS (archivo de eventos y errores)
# ==============================================================================
class GestorLogs:
    """Registra eventos y errores en un archivo de texto y por consola.

    Si el archivo no se puede escribir (permisos, disco lleno, etc.), el
    sistema NO se detiene: el error de escritura se ignora deliberadamente.
    """

    _RUTA_LOG = "software_fj_logs.log"  # Se crea en la carpeta de ejecucion

    @classmethod
    def _escribir(cls, nivel, mensaje):
        """Escribe una linea en el log con marca de tiempo."""
        linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {nivel}: {mensaje}\n"
        try:
            with open(cls._RUTA_LOG, "a", encoding="utf-8") as archivo:
                archivo.write(linea)
        except OSError:
            # No se puede escribir el log: no se interrumpe el sistema.
            pass
        print(f"   {nivel}: {mensaje}")

    @classmethod
    def evento(cls, mensaje):
        """Registra un evento informativo (operacion exitosa, inicio/fin)."""
        cls._escribir("INFO", mensaje)

    @classmethod
    def error(cls, mensaje, excepcion=None):
        """Registra un error. Si se pasa una excepcion, se anade su detalle."""
        if excepcion is not None:
            mensaje = f"{mensaje} -> {type(excepcion).__name__}: {excepcion}"
        cls._escribir("ERROR", mensaje)


# ==============================================================================
# 2. EXCEPCIONES PERSONALIZADAS (jerarquia propia del sistema)
# ==============================================================================
class ErrorSistemaBase(Exception):
    """Clase base de todas las excepciones del sistema Software FJ."""
    pass


class DatoInvalidoError(ErrorSistemaBase):
    """Se lanza cuando un dato no supera una validacion (formato, rango)."""
    pass


class ParametroFaltanteError(ErrorSistemaBase):
    """Se lanza cuando falta un parametro obligatorio o viene vacio."""
    pass


class OperacionNoPermitidaError(ErrorSistemaBase):
    """Se lanza cuando se intenta una accion no permitida en el estado actual."""
    pass


class ServicioNoDisponibleError(ErrorSistemaBase):
    """Se lanza cuando un servicio no existe o no esta disponible."""
    pass


class ClienteNoEncontradoError(ErrorSistemaBase):
    """Se lanza cuando se busca un cliente que no esta registrado."""
    pass


class ReservaInvalidaError(ErrorSistemaBase):
    """Se lanza cuando una reserva no se puede crear, confirmar o procesar."""
    pass


# ==============================================================================
# 3. CLASE ABSTRACTA DE ENTIDAD GENERAL (abstraccion + encapsulamiento)
# ==============================================================================
class Entidad(ABC):
    """Clase abstracta que representa cualquier entidad del sistema.

    Toda entidad tiene un identificador unico y un nombre, con validacion
    en los setters (encapsulamiento). Las clases hijas deben implementar
    describir().
    """

    def __init__(self, identificador, nombre):
        # Se usan las propiedades (setters) para que se ejecuten las validaciones
        self.identificador = identificador
        self.nombre = nombre

    # -- identificador -------------------------------------------------------
    @property
    def identificador(self):
        return self._identificador

    @identificador.setter
    def identificador(self, valor):
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El identificador no puede estar vacio.")
        self._identificador = str(valor).strip()

    # -- nombre --------------------------------------------------------------
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El nombre no puede estar vacio.")
        self._nombre = str(valor).strip()

    # -- metodo abstracto ----------------------------------------------------
    @abstractmethod
    def describir(self):
        """Devuelve una cadena legible que describe la entidad."""
        pass

    def __str__(self):
        return self.describir()


# ==============================================================================
# 4. CLASE CLIENTE (hereda de Entidad - validaciones robustas y encapsulamiento)
# ==============================================================================
class Cliente(Entidad):
    """Cliente de Software FJ. Sus datos personales estan encapsulados:
    solo se accede a traves de propiedades con validacion estricta."""

    def __init__(self, identificacion, nombre, email, telefono):
        super().__init__(identificacion, nombre)  # Valida identificacion y nombre
        self.email = email        # Dispara la validacion del setter
        self.telefono = telefono  # Dispara la validacion del setter

    # -- email ---------------------------------------------------------------
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        valor = str(valor).strip() if valor is not None else ""
        patron = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
        if not re.match(patron, valor):
            raise DatoInvalidoError(f"El correo '{valor}' no tiene un formato valido.")
        self._email = valor

    # -- telefono (incluye ENCADENAMIENTO de excepciones: raise ... from ...) -
    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        try:
            tel = str(valor).strip() if valor is not None else ""
            if not tel.isdigit():
                raise ValueError("El telefono solo debe contener digitos.")
            if len(tel) < 7:
                raise ValueError("El telefono debe tener al menos 7 digitos.")
        except ValueError as error_original:
            # Encadenamiento: la excepcion original se conserva con 'from'
            raise DatoInvalidoError(f"Telefono invalido: '{valor}'") from error_original
        self._telefono = tel

    # -- metodo abstracto implementado ---------------------------------------
    def describir(self):
        return (f"Cliente: {self.nombre} | ID: {self.identificador} | "
                f"Email: {self.email} | Tel: {self.telefono}")


# ==============================================================================
# 5. CLASE ABSTRACTA SERVICIO (base para los 3 servicios especializados)
# ==============================================================================
class Servicio(Entidad):
    """Clase abstracta de la que heredan todos los servicios de Software FJ.

    Define la interfaz comun: calcular_costo() (con parametros opcionales que
    simulan la sobrecarga de metodos), validar_parametros() y describir().
    """

    def __init__(self, codigo, nombre, costo_base):
        super().__init__(codigo, nombre)  # codigo = identificador del servicio
        self.costo_base = costo_base       # Valida que sea > 0
        self._disponible = True            # Por defecto el servicio esta activo

    # -- costo_base ----------------------------------------------------------
    @property
    def costo_base(self):
        return self._costo_base

    @costo_base.setter
    def costo_base(self, valor):
        try:
            valor = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(f"El costo base '{valor}' no es numerico.") from error_original
        if not math.isfinite(valor):
            raise DatoInvalidoError("El costo base debe ser un numero finito.")
        if valor <= 0:
            raise DatoInvalidoError(f"El costo base ({valor}) debe ser mayor que cero.")
        self._costo_base = valor

    # -- disponibilidad ------------------------------------------------------
    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, estado):
        if not isinstance(estado, bool):
            raise DatoInvalidoError("El estado de disponibilidad debe ser verdadero o falso.")
        self._disponible = estado

    # -- metodos abstractos que cada servicio HIJO debe implementar ----------
    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        """Calcula el costo del servicio.

        PARAMETROS OPCIONALES (sobrecarga en Python):
          * Si solo se pasa 'duracion' -> costo con impuesto por defecto (19%).
          * Si se pasa 'impuesto'      -> se aplica el impuesto indicado.
          * Si se pasa 'descuento'     -> se resta el descuento (proporcion 0..1).
        """
        pass

    @abstractmethod
    def validar_parametros(self, duracion, **kwargs):
        """Valida los parametros propios del servicio antes de reservar."""
        pass

    # -- describir() sigue abstracto: cada servicio lo describe a su modo ----
    # (se hereda de Entidad y se obliga a implementar en los hijos)


# ==============================================================================
# 5.1 SERVICIO ESPECIALIZADO 1: RESERVA DE SALAS
# ==============================================================================
class ReservaSalas(Servicio):
    """Alquiler de salas de reuniones. La duracion se mide en HORAS."""

    def __init__(self, codigo, nombre, costo_base, capacidad):
        super().__init__(codigo, nombre, costo_base)
        self.capacidad = capacidad  # Numero de personas que caben en la sala

    @property
    def capacidad(self):
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor):
        try:
            capacidad_num = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La capacidad de la sala '{valor}' no es un numero entero valido."
            ) from error_original
        if not math.isfinite(capacidad_num) or not capacidad_num.is_integer():
            raise DatoInvalidoError(
                f"La capacidad de la sala '{valor}' no es un numero entero valido."
            )
        capacidad = int(capacidad_num)
        if capacidad <= 0:
            raise DatoInvalidoError("La capacidad de la sala debe ser mayor que cero.")
        self._capacidad = capacidad

    def validar_parametros(self, duracion, **kwargs):
        try:
            duracion_num = float(duracion)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La duracion de la sala '{duracion}' debe ser numerica."
            ) from error_original
        if not math.isfinite(duracion_num):
            raise DatoInvalidoError("La duracion de la sala debe ser un numero finito.")
        if duracion_num <= 0:
            raise DatoInvalidoError("La duracion de la sala debe ser mayor que 0 horas.")
        if duracion_num > 24:
            raise DatoInvalidoError("Una sala no se puede reservar mas de 24 horas.")

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        self.validar_parametros(duracion)
        try:
            descuento_num = float(descuento)
            impuesto_num = float(impuesto)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                "El impuesto y el descuento deben ser valores numericos."
            ) from error_original
        if not math.isfinite(descuento_num) or not math.isfinite(impuesto_num):
            raise DatoInvalidoError("El impuesto y el descuento deben ser numeros finitos.")
        if descuento_num < 0 or descuento_num > 1:
            raise DatoInvalidoError("El descuento debe estar entre 0 y 1.")
        if impuesto_num < 0:
            raise DatoInvalidoError("El impuesto no puede ser negativo.")
        duracion_num = float(duracion)
        subtotal = duracion_num * self.costo_base
        subtotal -= subtotal * descuento_num   # Se aplica el descuento (0..1)
        total = subtotal * (1 + impuesto_num)  # Se aplica el impuesto
        return round(total, 2)

    def describir(self):
        return (f"[Reserva de Salas] {self.nombre} | Cod: {self.identificador} | "
                f"Capacidad: {self.capacidad} pers. | Costo base: ${self.costo_base}/hora")


# ==============================================================================
# 5.2 SERVICIO ESPECIALIZADO 2: ALQUILER DE EQUIPOS
# ==============================================================================
class AlquilerEquipos(Servicio):
    """Alquiler de equipos (computadores, proyectores, etc.).
    La duracion se mide en DIAS y se multiplica por la cantidad de equipos."""

    def __init__(self, codigo, nombre, costo_base, tipo_equipo, cantidad):
        super().__init__(codigo, nombre, costo_base)
        if tipo_equipo is None or not str(tipo_equipo).strip():
            raise DatoInvalidoError("El tipo de equipo no puede estar vacio.")
        tipo_equipo = str(tipo_equipo).strip()
        self.tipo_equipo = tipo_equipo
        self.cantidad = cantidad

    @property
    def cantidad(self):
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor):
        try:
            cantidad_num = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La cantidad de equipos '{valor}' no es un numero entero valido."
            ) from error_original
        if not math.isfinite(cantidad_num) or not cantidad_num.is_integer():
            raise DatoInvalidoError(
                f"La cantidad de equipos '{valor}' no es un numero entero valido."
            )
        cantidad = int(cantidad_num)
        if cantidad <= 0:
            raise DatoInvalidoError("La cantidad de equipos debe ser mayor que cero.")
        self._cantidad = cantidad

    def validar_parametros(self, duracion, **kwargs):
        try:
            duracion_num = float(duracion)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"Los dias de alquiler '{duracion}' deben ser numericos."
            ) from error_original
        if not math.isfinite(duracion_num):
            raise DatoInvalidoError("Los dias de alquiler deben ser un numero finito.")
        if duracion_num <= 0:
            raise DatoInvalidoError("Los dias de alquiler deben ser mayores que cero.")

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        self.validar_parametros(duracion)
        try:
            descuento_num = float(descuento)
            impuesto_num = float(impuesto)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                "El impuesto y el descuento deben ser valores numericos."
            ) from error_original
        if not math.isfinite(descuento_num) or not math.isfinite(impuesto_num):
            raise DatoInvalidoError("El impuesto y el descuento deben ser numeros finitos.")
        if descuento_num < 0 or descuento_num > 1:
            raise DatoInvalidoError("El descuento debe estar entre 0 y 1.")
        if impuesto_num < 0:
            raise DatoInvalidoError("El impuesto no puede ser negativo.")
        duracion_num = float(duracion)
        subtotal = duracion_num * self.costo_base * self.cantidad
        subtotal -= subtotal * descuento_num
        total = subtotal * (1 + impuesto_num)
        return round(total, 2)

    def describir(self):
        return (f"[Alquiler de Equipos] {self.nombre} | Cod: {self.identificador} | "
                f"Tipo: {self.tipo_equipo} | Cant: {self.cantidad} | "
                f"Costo base: ${self.costo_base}/equipo/dia")


# ==============================================================================
# 5.3 SERVICIO ESPECIALIZADO 3: ASESORIA ESPECIALIZADA
# ==============================================================================
class AsesoriaEspecializada(Servicio):
    """Asesoria tecnica especializada. La duracion se mide en HORAS y tiene
    una duracion minima obligatoria (por defecto 2 horas)."""

    def __init__(self, codigo, nombre, costo_base, area, asesor, duracion_minima=2):
        super().__init__(codigo, nombre, costo_base)
        if area is None or not str(area).strip():
            raise DatoInvalidoError("El area de la asesoria no puede estar vacia.")
        if asesor is None or not str(asesor).strip():
            raise DatoInvalidoError("El nombre del asesor no puede estar vacio.")
        area = str(area).strip()
        asesor = str(asesor).strip()
        self.area = area
        self.asesor = asesor
        self.duracion_minima = duracion_minima

    @property
    def duracion_minima(self):
        return self._duracion_minima

    @duracion_minima.setter
    def duracion_minima(self, valor):
        try:
            duracion = float(valor)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La duracion minima '{valor}' debe ser numerica."
            ) from error_original
        if not math.isfinite(duracion):
            raise DatoInvalidoError("La duracion minima debe ser un numero finito.")
        if duracion <= 0:
            raise DatoInvalidoError("La duracion minima debe ser mayor que cero.")
        self._duracion_minima = duracion

    def validar_parametros(self, duracion, **kwargs):
        try:
            duracion_num = float(duracion)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La duracion de la asesoria '{duracion}' debe ser numerica."
            ) from error_original
        if not math.isfinite(duracion_num):
            raise DatoInvalidoError("La duracion de la asesoria debe ser un numero finito.")
        if duracion_num < self.duracion_minima:
            raise DatoInvalidoError(
                f"La asesoria '{self.nombre}' requiere minimo {self.duracion_minima} horas "
                f"(se indicaron {duracion}).")

    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        self.validar_parametros(duracion)
        try:
            descuento_num = float(descuento)
            impuesto_num = float(impuesto)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                "El impuesto y el descuento deben ser valores numericos."
            ) from error_original
        if not math.isfinite(descuento_num) or not math.isfinite(impuesto_num):
            raise DatoInvalidoError("El impuesto y el descuento deben ser numeros finitos.")
        if descuento_num < 0 or descuento_num > 1:
            raise DatoInvalidoError("El descuento debe estar entre 0 y 1.")
        if impuesto_num < 0:
            raise DatoInvalidoError("El impuesto no puede ser negativo.")
        duracion_num = float(duracion)
        subtotal = duracion_num * self.costo_base  # Tarifa por hora del asesor
        subtotal -= subtotal * descuento_num
        total = subtotal * (1 + impuesto_num)
        return round(total, 2)

    def describir(self):
        return (f"[Asesoria Especializada] {self.nombre} | Cod: {self.identificador} | "
                f"Area: {self.area} | Asesor: {self.asesor} | "
                f"Costo base: ${self.costo_base}/hora (min. {self.duracion_minima}h)")


# ==============================================================================
# 6. CLASE RESERVA (integra cliente + servicio + duracion + estado)
# ==============================================================================
class Reserva:
    """Reserva de un servicio para un cliente. Gestiona su ciclo de vida:
    PENDIENTE -> CONFIRMADA / CANCELADA -> FINALIZADA."""

    _contador_id = 1  # Auto-incremental para generar codigos de reserva

    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente):
            raise ParametroFaltanteError("Se requiere un objeto Cliente valido para la reserva.")
        if not isinstance(servicio, Servicio):
            raise ParametroFaltanteError("Se requiere un objeto Servicio valido para la reserva.")
        try:
            duracion_num = float(duracion)
        except (TypeError, ValueError) as error_original:
            raise DatoInvalidoError(
                f"La duracion '{duracion}' debe ser numerica para crear la reserva."
            ) from error_original
        if not math.isfinite(duracion_num):
            raise DatoInvalidoError("La duracion de la reserva debe ser un numero finito.")
        if duracion_num <= 0:
            raise DatoInvalidoError("La duracion de la reserva debe ser mayor que cero.")
        self._numero = Reserva._contador_id
        self._id = f"R-{self._numero:04d}"
        Reserva._contador_id += 1
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion_num
        self._estado = "PENDIENTE"
        self._costo_total = 0.0
        self._fecha_creacion = datetime.now()

    # -- propiedades de solo lectura (encapsulamiento) -----------------------
    @property
    def id_reserva(self):
        return self._id

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    # -- procesar: calcula el costo (puede lanzar excepciones) ---------------
    def procesar(self):
        """Valida parametros del servicio y calcula el costo total.
        Usa encadenamiento: un error de validacion se reporta como ReservaInvalidaError."""
        if self._estado not in ("PENDIENTE", "CONFIRMADA"):
            raise OperacionNoPermitidaError(
                f"La reserva {self._id} no se puede procesar: su estado es {self._estado}.")
        try:
            self._costo_total = self._servicio.calcular_costo(self._duracion)
        except DatoInvalidoError as error_original:
            raise ReservaInvalidaError(
                f"Reserva {self._id}: parametros invalidos para el servicio.") from error_original
        return self._costo_total

    # -- confirmar -----------------------------------------------------------
    def confirmar(self):
        if self._estado != "PENDIENTE":
            raise OperacionNoPermitidaError(
                f"La reserva {self._id} no se puede confirmar: su estado es {self._estado}.")
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._servicio.nombre}' no esta disponible.")
        self.procesar()  # Calcula el costo; puede lanzar ReservaInvalidaError
        self._estado = "CONFIRMADA"

    # -- cancelar ------------------------------------------------------------
    def cancelar(self):
        if self._estado in ("CANCELADA", "FINALIZADA"):
            raise OperacionNoPermitidaError(
                f"La reserva {self._id} ya esta {self._estado}; no se puede cancelar.")
        self._estado = "CANCELADA"

    # -- describir -----------------------------------------------------------
    def describir(self):
        return (f"Reserva {self._id} | Estado: {self._estado} | "
                f"Cliente: {self._cliente.nombre} | Servicio: {self._servicio.nombre} | "
                f"Duracion: {self._duracion} | Costo total: ${self._costo_total}")

    def __str__(self):
        return self.describir()


# ==============================================================================
# 7. SISTEMA DE GESTION (fachada: listas internas + operaciones + menu)
# ==============================================================================
class SistemaGestion:
    """Controlador principal. Mantiene en memoria (sin BD) los clientes,
    servicios y reservas, y orquesta todas las operaciones con manejo de
    excepciones y registro en el log."""

    def __init__(self):
        self._clientes = {}   # dict: identificacion -> Cliente
        self._servicios = {}  # dict: codigo -> Servicio
        self._reservas = []   # lista de objetos Reserva
        GestorLogs.evento("Sistema Software FJ inicializado.")

    # ------------------------------------------------------------------
    # 7.1 Registrar cliente (demuestra try/except/else/finally completo)
    # ------------------------------------------------------------------
    def registrar_cliente(self, identificacion, nombre, email, telefono):
        try:
            identificacion = str(identificacion).strip()
            if identificacion in self._clientes:
                raise OperacionNoPermitidaError(
                    f"Ya existe un cliente con identificacion {identificacion}.")
            cliente = Cliente(identificacion, nombre, email, telefono)
        except ErrorSistemaBase as error:
            GestorLogs.error("Fallo el registro de cliente", error)
            raise  # Se relanza para que quien llama lo maneje
        else:
            # El bloque else se ejecuta SOLO si NO hubo excepcion
            self._clientes[identificacion] = cliente
            GestorLogs.evento(f"Cliente registrado: {cliente.nombre} (ID {identificacion})")
            return cliente
        finally:
            # El bloque finally se ejecuta SIEMPRE (haya o no error)
            GestorLogs.evento(f"Finalizo operacion: registrar_cliente({identificacion})")

    # ------------------------------------------------------------------
    # 7.2 Crear servicio (fabrica polimorfica segun el tipo)
    # ------------------------------------------------------------------
    def crear_servicio(self, tipo, codigo, nombre, costo_base, **kwargs):
        try:
            codigo = str(codigo).strip()
            if codigo in self._servicios:
                raise OperacionNoPermitidaError(f"Ya existe un servicio con codigo {codigo}.")
            tipo = str(tipo).strip().lower()
            if tipo == "sala":
                servicio = ReservaSalas(codigo, nombre, costo_base,
                                        capacidad=kwargs.get("capacidad", 10))
            elif tipo == "equipo":
                servicio = AlquilerEquipos(codigo, nombre, costo_base,
                                           tipo_equipo=kwargs.get("tipo_equipo", "Generico"),
                                           cantidad=kwargs.get("cantidad", 1))
            elif tipo == "asesoria":
                servicio = AsesoriaEspecializada(codigo, nombre, costo_base,
                                                 area=kwargs.get("area", "General"),
                                                 asesor=kwargs.get("asesor", "Por asignar"),
                                                 duracion_minima=kwargs.get("duracion_minima", 2))
            else:
                raise DatoInvalidoError(
                    f"Tipo de servicio '{tipo}' invalido. Use: sala, equipo o asesoria.")
        except ErrorSistemaBase as error:
            GestorLogs.error("Fallo la creacion del servicio", error)
            raise
        else:
            self._servicios[codigo] = servicio
            GestorLogs.evento(f"Servicio creado ({tipo}): {servicio.nombre} (Cod {codigo})")
            return servicio
        finally:
            GestorLogs.evento(f"Finalizo operacion: crear_servicio({codigo})")

    # ------------------------------------------------------------------
    # 7.3 Busquedas (lanzan excepciones propias si no encuentran)
    # ------------------------------------------------------------------
    def buscar_cliente(self, identificacion):
        identificacion = str(identificacion).strip()
        if identificacion not in self._clientes:
            raise ClienteNoEncontradoError(f"El cliente {identificacion} no esta registrado.")
        return self._clientes[identificacion]

    def buscar_servicio(self, codigo):
        codigo = str(codigo).strip()
        if codigo not in self._servicios:
            raise ServicioNoDisponibleError(f"El servicio {codigo} no existe.")
        if not self._servicios[codigo].disponible:
            raise ServicioNoDisponibleError(f"El servicio {codigo} no esta disponible.")
        return self._servicios[codigo]

    # ------------------------------------------------------------------
    # 7.4 Crear reserva (con encadenamiento de excepciones)
    # ------------------------------------------------------------------
    def crear_reserva(self, identificacion_cliente, codigo_servicio, duracion):
        reserva = None
        try:
            cliente = self.buscar_cliente(identificacion_cliente)
            servicio = self.buscar_servicio(codigo_servicio)
            reserva = Reserva(cliente, servicio, duracion)
            reserva.confirmar()  # Puede lanzar OperacionNoPermitidaError / etc.
        except (ClienteNoEncontradoError, ServicioNoDisponibleError) as error_original:
            # Encadenamiento: el error de origen se conserva dentro del nuevo
            raise ReservaInvalidaError(
                "No se pudo crear la reserva: cliente o servicio invalidos."
            ) from error_original
        except ErrorSistemaBase as error:
            if reserva is not None and reserva not in self._reservas:
                if getattr(reserva, "_numero", None) == Reserva._contador_id - 1:
                    Reserva._contador_id -= 1
            GestorLogs.error("Fallo la creacion de la reserva", error)
            raise
        else:
            self._reservas.append(reserva)
            GestorLogs.evento(
                f"Reserva creada y confirmada: {reserva.id_reserva} "
                f"(costo ${reserva.costo_total})")
            return reserva
        finally:
            GestorLogs.evento(
                f"Finalizo operacion: crear_reserva({identificacion_cliente}, {codigo_servicio})")

    # ------------------------------------------------------------------
    # 7.5 Cancelar reserva
    # ------------------------------------------------------------------
    def cancelar_reserva(self, id_reserva):
        try:
            id_reserva = str(id_reserva).strip().upper()
            reserva = next((r for r in self._reservas if r.id_reserva == id_reserva), None)
            if reserva is None:
                raise ReservaInvalidaError(f"La reserva {id_reserva} no existe.")
            reserva.cancelar()  # Puede lanzar OperacionNoPermitidaError
        except ErrorSistemaBase as error:
            GestorLogs.error("Fallo la cancelacion de la reserva", error)
            raise
        else:
            GestorLogs.evento(f"Reserva cancelada: {id_reserva}")
            return reserva
        finally:
            GestorLogs.evento(f"Finalizo operacion: cancelar_reserva({id_reserva})")

    # ------------------------------------------------------------------
    # 7.6 Listados
    # ------------------------------------------------------------------
    def listar_clientes(self):
        if not self._clientes:
            return "No hay clientes registrados."
        return "\n".join("  " + c.describir() for c in self._clientes.values())

    def listar_servicios(self):
        if not self._servicios:
            return "No hay servicios registrados."
        return "\n".join("  " + s.describir() for s in self._servicios.values())

    def listar_reservas(self):
        if not self._reservas:
            return "No hay reservas registradas."
        return "\n".join("  " + r.describir() for r in self._reservas)

    # ------------------------------------------------------------------
    # 7.7 SIMULACION AUTOMATICA (mas de 10 operaciones validas e invalidas)
    # ------------------------------------------------------------------
    def _prueba(self, numero, descripcion, funcion):
        """Ejecuta una operacion de prueba y atrapa sus excepciones para que el
        sistema NUNCA se detenga. Demuestra el manejo controlado de errores."""
        print(f"\n--- Prueba {numero}: {descripcion} ---")
        try:
            resultado = funcion()
        except ErrorSistemaBase as error:
            GestorLogs.error(f"Prueba {numero} fallo (error controlado)", error)
            print(f"   [ERROR CONTROLADO] {type(error).__name__}: {error}")
            print("   (el sistema continua funcionando)")
        except Exception as error:
            GestorLogs.error(f"Prueba {numero} fallo por un error inesperado", error)
            print(f"   [ERROR INESPERADO CONTROLADO] {type(error).__name__}: {error}")
            print("   (el sistema continua funcionando)")
        else:
            texto = str(resultado) if resultado is not None else "Operacion exitosa."
            print(f"   [OK] {texto}")

    def ejecutar_simulacion(self):
        """Ejecuta mas de 10 operaciones completas (validas e invalidas)."""
        print("\n" + "=" * 70)
        print("INICIO DE LA SIMULACION AUTOMATICA (>= 10 operaciones)")
        print("=" * 70)

        # 1. Cliente valido
        self._prueba(1, "Registrar cliente valido (Maria Perez)",
                     lambda: self.registrar_cliente("1020", "Maria Perez",
                                                    "maria@correo.com", "3101234567"))
        # 2. Cliente con email invalido -> error controlado
        self._prueba(2, "Registrar cliente con email invalido (sin @)",
                     lambda: self.registrar_cliente("1030", "Carlos Ruiz",
                                                    "carlos.correo.com", "3117654321"))
        # 3. Cliente valido 2
        self._prueba(3, "Registrar cliente valido (Juan Gomez)",
                     lambda: self.registrar_cliente("1040", "Juan Gomez",
                                                    "juan@empresa.com", "3209876543"))
        # 4. Cliente con telefono invalido (letras) -> error controlado
        self._prueba(4, "Registrar cliente con telefono invalido (contiene letras)",
                     lambda: self.registrar_cliente("1050", "Ana Torres",
                                                    "ana@correo.com", "31abc567"))
        # 5. Servicio valido: reserva de sala
        self._prueba(5, "Crear servicio valido: Reserva de Sala (capacidad 20)",
                     lambda: self.crear_servicio("sala", "S01", "Sala de Juntas Principal",
                                                 50000, capacidad=20))
        # 6. Servicio con costo base negativo -> error controlado
        self._prueba(6, "Crear servicio con costo base negativo (invalido)",
                     lambda: self.crear_servicio("equipo", "S02", "Proyector X",
                                                 -1000, tipo_equipo="Proyector", cantidad=1))
        # 7. Servicio valido: alquiler de equipos
        self._prueba(7, "Crear servicio valido: Alquiler de Equipos (5 laptops)",
                     lambda: self.crear_servicio("equipo", "S03", "Laptop empresarial",
                                                 20000, tipo_equipo="Laptop", cantidad=5))
        # 8. Servicio valido: asesoria especializada
        self._prueba(8, "Crear servicio valido: Asesoria en seguridad informatica",
                     lambda: self.crear_servicio("asesoria", "S04", "Auditoria de Seguridad",
                                                 120000, area="Seguridad TI",
                                                 asesor="Ing. Perez", duracion_minima=3))
        # 9. Servicio de tipo inexistente -> error controlado
        self._prueba(9, "Crear servicio de tipo inexistente ('transporte')",
                     lambda: self.crear_servicio("transporte", "S05", "Flete", 30000))
        # 10. Reserva exitosa (cliente 1020 + sala S01, 2 horas)
        self._prueba(10, "Crear reserva exitosa: Maria - Sala S01 por 2 horas",
                     lambda: self.crear_reserva("1020", "S01", 2))
        # 11. Reserva con cliente inexistente -> error controlado (encadenamiento)
        self._prueba(11, "Crear reserva con cliente no registrado (9999)",
                     lambda: self.crear_reserva("9999", "S01", 2))
        # 12. Reserva con duracion negativa -> error controlado
        self._prueba(12, "Crear reserva con duracion negativa (-3)",
                     lambda: self.crear_reserva("1040", "S03", -3))
        # 13. Reserva de asesoria con duracion menor al minimo -> error controlado
        self._prueba(13, "Crear reserva de asesoria de 1 hora (minimo 3)",
                     lambda: self.crear_reserva("1040", "S04", 1))
        # 14. Cancelar reserva existente (la R-0001 creada en la prueba 10)
        self._prueba(14, "Cancelar la reserva R-0001 (existente y pendiente/confirmada)",
                     lambda: self.cancelar_reserva("R-0001"))
        # 15. Cancelar nuevamente la misma reserva -> error controlado
        self._prueba(15, "Intentar cancelar de nuevo la reserva R-0001 (ya cancelada)",
                     lambda: self.cancelar_reserva("R-0001"))

        print("\n" + "=" * 70)
        print("FIN DE LA SIMULACION - el sistema siguio funcionando pese a los errores")
        print("=" * 70)
        print("\n-- Estado final del sistema --")
        print("Clientes:\n" + self.listar_clientes())
        print("Servicios:\n" + self.listar_servicios())
        print("Reservas:\n" + self.listar_reservas())
        print(f"\nLos eventos y errores quedaron registrados en: {GestorLogs._RUTA_LOG}")


# ==============================================================================
# 8. MENU INTERACTIVO Y FUNCION PRINCIPAL
# ==============================================================================
def mostrar_bienvenida():
    """Imprime el encabezado del sistema (aportado por el Compañero 1)."""
    print("BIENVENIDOS A LA FASE 4")
    print("SOFTWARE FJ")
    print("Sistema de Gestión de Clientes y Reservas")


def mostrar_menu():
    print("\n" + "-" * 50)
    print("MENU PRINCIPAL - SOFTWARE FJ")
    print("-" * 50)
    print(" 1. Registrar cliente")
    print(" 2. Crear servicio")
    print(" 3. Crear reserva")
    print(" 4. Cancelar reserva")
    print(" 5. Listar clientes")
    print(" 6. Listar servicios")
    print(" 7. Listar reservas")
    print(" 8. Ejecutar simulacion automatica (>= 10 operaciones)")
    print(" 0. Salir")
    print("-" * 50)


def leer_entero(mensaje):
    """Lee un entero de forma segura; repite hasta que sea valido."""
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("   Por favor ingrese un numero entero valido.")


def menu_registrar_cliente(sistema):
    identificacion = input("  Identificacion: ").strip()
    nombre = input("  Nombre completo: ").strip()
    email = input("  Email: ").strip()
    telefono = input("  Telefono: ").strip()
    try:
        sistema.registrar_cliente(identificacion, nombre, email, telefono)
        print("   Cliente registrado con exito.")
    except ErrorSistemaBase as error:
        print(f"   No se pudo registrar: {error}")


def menu_crear_servicio(sistema):
    print("   Tipos: 1=Sala  2=Equipo  3=Asesoria")
    tipo_num = leer_entero("   Tipo de servicio: ")
    tipos = {1: "sala", 2: "equipo", 3: "asesoria"}
    if tipo_num not in tipos:
        print("   Tipo invalido.")
        return
    codigo = input("   Codigo: ").strip()
    nombre = input("   Nombre del servicio: ").strip()
    costo = input("   Costo base: ").strip()
    try:
        if tipo_num == 1:
            capacidad = leer_entero("   Capacidad (personas): ")
            sistema.crear_servicio("sala", codigo, nombre, costo, capacidad=capacidad)
        elif tipo_num == 2:
            tipo_eq = input("   Tipo de equipo: ").strip()
            cantidad = leer_entero("   Cantidad: ")
            sistema.crear_servicio("equipo", codigo, nombre, costo,
                                   tipo_equipo=tipo_eq, cantidad=cantidad)
        else:
            area = input("   Area: ").strip()
            asesor = input("   Nombre del asesor: ").strip()
            sistema.crear_servicio("asesoria", codigo, nombre, costo,
                                   area=area, asesor=asesor)
        print("   Servicio creado con exito.")
    except ErrorSistemaBase as error:
        print(f"   No se pudo crear el servicio: {error}")


def menu_crear_reserva(sistema):
    id_cliente = input("  Identificacion del cliente: ").strip()
    cod_servicio = input("  Codigo del servicio: ").strip()
    duracion = input("  Duracion (horas o dias segun el servicio): ").strip()
    try:
        reserva = sistema.crear_reserva(id_cliente, cod_servicio, float(duracion))
        print(f"   Reserva creada: {reserva}")
    except ErrorSistemaBase as error:
        print(f"   No se pudo crear la reserva: {error}")
    except ValueError:
        print("   La duracion debe ser numerica.")


def menu_cancelar_reserva(sistema):
    id_reserva = input("  Codigo de reserva (ej. R-0001): ").strip()
    try:
        sistema.cancelar_reserva(id_reserva)
        print("   Reserva cancelada con exito.")
    except ErrorSistemaBase as error:
        print(f"   No se pudo cancelar: {error}")


def main():
    mostrar_bienvenida()
    sistema = SistemaGestion()

    # Si se ejecuta con el argumento --demo, corre la simulacion y sale.
    if "--demo" in sys.argv:
        sistema.ejecutar_simulacion()
        return

    while True:
        mostrar_menu()
        try:
            opcion = leer_entero("Seleccione una opcion: ")
            if opcion == 0:
                print("Gracias por usar el sistema Software FJ.")
                break
            elif opcion == 1:
                menu_registrar_cliente(sistema)
            elif opcion == 2:
                menu_crear_servicio(sistema)
            elif opcion == 3:
                menu_crear_reserva(sistema)
            elif opcion == 4:
                menu_cancelar_reserva(sistema)
            elif opcion == 5:
                print(sistema.listar_clientes())
            elif opcion == 6:
                print(sistema.listar_servicios())
            elif opcion == 7:
                print(sistema.listar_reservas())
            elif opcion == 8:
                sistema.ejecutar_simulacion()
            else:
                print("Opcion no valida, intente de nuevo.")
        except ErrorSistemaBase as error:
            # Captura cualquier error del sistema y mantiene viva la aplicacion
            GestorLogs.error("Error en el menu principal (recuperado)", error)
            print(f"Ocurrio un error controlado: {error}. El sistema continua.")


# ==============================================================================
# 9. PUNTO DE ENTRADA (nivel superior con proteccion total ante excepciones)
# ==============================================================================
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nOperacion interrumpida por el usuario. El sistema se cerrara.")
        GestorLogs.evento("Sistema cerrado por interrupcion del usuario.")
    except Exception as error_inesperado:
        # Ultimo nivel de seguridad: registra y controla excepciones no previstas.
        GestorLogs.error("ERROR INESPERADO recuperado en el nivel superior",
                         error_inesperado)
        print("El sistema se cerro tras recuperar un error inesperado.")
    finally:
        GestorLogs.evento("Sistema Software FJ cerrado.")
