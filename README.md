
# Estacionamiento Central

**Estacionamiento Central** es una aplicación de escritorio para Windows que permite gestionar de forma eficiente un estacionamiento con entradas/salidas de vehículos, cobros automáticos, generación de tickets, reportes y cierres diarios. Está diseñada para equipos con recursos limitados y es compatible con impresoras térmicas Bluetooth de 58mm.

---

## Descripción

Este software fue desarrollado como parte del proyecto de título técnico en análisis y programación computacional de IACC. El objetivo es modernizar la gestión de estacionamientos optimizando el registro de vehículos, cálculo de tarifas y control administrativo, incluyendo:

- Registro de ingresos y salidas
- Cálculo automático de tarifas por minuto, tramo o mensualidad
- Emisión de tickets térmicos
- Generación de reportes filtrables en PDF
- Control de usuarios (operador, administrador)
- Asistencias de personal
- Cierres diarios y mensuales

---

## Tecnologías Utilizadas

- **Lenguaje principal**: Python 3.11+
- **Interfaz gráfica**: PySide6 (Qt para Python)
- **Base de datos**: MySQL
- **ORM/Conexión**: `mysql-connector-python`
- **Estilo PDF**: FPDF
- **Estilos visuales**: QSS (Qt Style Sheets)
- **Control de versiones**: Git & GitHub

---

## Requisitos del Sistema

- Sistema Operativo: Windows 10 u 11
- Procesador: 2 GHz o superior
- Memoria RAM: 4GB mínimo
- Espacio disponible en disco: al l menos 1 GB
- Sumatra PDF (para impresión directa)
- Impresora térmica de 58mm (opcional)

---

## Instalación Paso a Paso

---

### 1. Requisitos del sistema

Antes de iniciar la instalación, se debe verificar que el equipo cumpla con los siguientes requisitos:

**Requisitos de hardware**
- Procesador de 2 GHz o superior
- Memoria RAM mínima de 4 GB
- Espacio disponible en disco de al menos 1 GB

**Requisitos de software**
- Sistema operativo Windows 10 o superior
- Permisos de administrador en el equipo
- Impresora térmica previamente instalada en el sistema operativo

El sistema no requiere instalación previa de Python ni MySQL, ya que estos componentes son gestionados automáticamente por el instalador.

---

### 2. Obtención del instalador

El instalador del sistema se distribuye mediante el siguiente archivo ejecutable:

**Instalador_EstacionamientoCentral.exe**
Descarga directa: https://www.mediafire.com/file/ree1fdfj0uh81qr/Instalador_EstacionamientoCentral.exe/file

**Repositorio del proyecto** 
https://github.com/matiasrmb/estacionamiento-central

En algunos casos, al descargar el archivo desde internet (por ejemplo, mediante MediaFire), el sistema operativo puede mostrar advertencias de seguridad indicando que el archivo podría ser potencialmente peligroso.

Esto se debe a que el instalador contiene múltiples componentes y scripts de automatización.

En caso de presentarse este mensaje, se recomienda:

- Desactivar temporalmente la protección en tiempo real del antivirus
- Ejecutar el instalador manualmente con permisos de administrador

Una vez finalizada la instalación, se puede reactivar la protección del sistema.

---

### 3. Ejecución del instalador

Para iniciar la instalación:

1. Ubicar el archivo Instalador_EstacionamientoCentral.exe
2. Hacer clic derecho sobre el archivo
3. Seleccionar la opción “Ejecutar como administrador”

Se iniciará el asistente de instalación del sistema.

---

### 4. Proceso de instalación

El instalador guía al usuario mediante una serie de pasos automáticos.  

Durante este proceso, el sistema realiza las siguientes acciones:

---

#### 4.1 Copia de archivos

El instalador copia todos los archivos del sistema en la siguiente ruta:
C:\EstacionamientoCentral


En esta ubicación se incluyen:

- Ejecutable del sistema  
- Archivos de configuración  
- Estructura de base de datos  
- Carpetas de almacenamiento (tickets, reportes, etc.)  

---

#### 4.2 Instalación y configuración de MySQL

El instalador verifica si MySQL está presente en el sistema.

**Si MySQL no está instalado:**
- Se extrae automáticamente una versión incluida del servidor MySQL  
- Se configura el servicio **MySQL80**  
- Se inicializa el motor de base de datos  

**Si MySQL ya está instalado:**
- Se reutiliza la instalación existente  
- Se verifica el estado del servicio  
- Se inicia el servicio si es necesario  

---

#### 4.3 Creación de la base de datos

El instalador verifica la existencia de la base de datos:
estacionamiento_db

- Si la base de datos no existe:
  - Se crea automáticamente  
  - Se importa la estructura desde el archivo SQL  

- Si ya existe:
  - Se mantiene sin eliminar la información existente  

---

#### 4.4 Creación del usuario de aplicación

El sistema crea automáticamente un usuario en MySQL para el funcionamiento de la aplicación:

- **Usuario:** `estacionamiento_app`  
- **Contraseña:** `ec_app_2026`  

Este usuario es utilizado internamente por el sistema para conectarse a la base de datos.

---

#### 4.5 Configuración del sistema

El instalador genera automáticamente el archivo de configuración:
C:\EstacionamientoCentral_internal\config.ini

Este archivo contiene los parámetros necesarios para la conexión a la base de datos.

---

#### 4.6 Instalación de visor PDF

El instalador **no incluye** la instalación de SumatraPDF, el cual es utilizado para gestionar la visualización e impresión de tickets.

Por tanto, se debe descargar desde su página oficial:

https://www.sumatrapdfreader.org/download-free-pdf-viewer  

Luego seguir los pasos estándar de instalación.

---

#### 4.7 Creación de accesos directos

El instalador crea:

- Acceso directo en el menú inicio  
- Acceso directo en el escritorio (opcional)  

---

### 5. Finalización de la instalación

Al finalizar el proceso, el instalador ofrece la opción:

- **“Ejecutar Estacionamiento Central”**

Si el usuario selecciona esta opción, el sistema se abrirá automáticamente.

### 5.Crear base de datos y tablas

Puedes ejecutar el script SQL incluido 'schema.sql'

---

## Uso del Sistema


### 1. Iniciar sesión como operador o administrador.

### 2. Acceder a las siguientes funcionalidades desde el panel principal:

- Ingresar vehículos (y emitir ticket)
- Registrar salida (y emitir ticket con cálculo)
- Ver vehículos activos
- Generar reportes de ingresos/salidas
- Generar reportes de asistencias
- Realizar cierres diarios o mensuales
- Administrar usuarios
- Cambiar configuración del sistema

---

## Estructura del Proyecto

```graphql
estacionamiento-central/
|   config.ini
|   crear_usuario.py
|   EstacionamientoCentral.spec
|   estructura_limpia.txt
|   main.py
|   README.md
|   requirements.txt
|   schema.sql
+---asistencias
+---cierres
+---controllers
|   |   asistencias_controller.py
|   |   cierres_controller.py
|   |   config_controller.py
|   |   dashboard_controller.py
|   |   login_controller.py
|   |   mensuales_controller.py
|   |   registro_controller.py
|   |   reportes_controller.py
|   |   subida_controller.py
|   |   tarifas_controller.py
|   |   usuarios_controller.py
|   |  
+---pdfs
+---reportes
+---tickets
+---utils
|   |   crear_admin.py
|   |   db.py
|   |   pdf.py
|   |   pdf_asistencias.py
|   |   pdf_utils.py
|   |   ticket.py
|   |   __init__.py
|   | 
+---views
|   |   admin_edicion.py
|   |   asistencias.py
|   |   configuracion.py
|   |   dashboard.py
|   |   login.py
|   |   main_window.py
|   |   mensuales.py
|   |   registro.py
|   |   reportes.py
|   |   setup_window.py
|   |   subida_dialog.py
|   |   tarifas_personalizadas.py
|   |   usuarios.py

```
## Público Objetivo

Este proyecto fue desarrollado pensando en:

- Profesores evaluadores del proceso de titulación.
- Desarrolladores Python que deseen estudiar una arquitectura modular y funcional.
- Dueños de estacionamientos que necesitan una solución sencilla, económica y práctica.
## Captura del funcionamiento



## Créditos

- Desarrollador principal: Matías Román Medina Becerra
- Institución: Instituto Profesional IACC
- Proyecto de Título: Técnico de Nivel Superior en Análisis y Programación Computacional
- Año: 2025
