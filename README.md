# Estacionamiento Central

**Estacionamiento Central** es una aplicación de escritorio para Windows orientada a la gestión eficiente de estacionamientos vehiculares. Permite registrar ingresos y salidas, calcular tarifas automáticamente, generar tickets, emitir reportes y realizar cierres operacionales.

El sistema está optimizado para funcionar en equipos de bajos recursos y es compatible con impresoras térmicas de 58mm.

---

## Descripción

Este software fue desarrollado como parte del proyecto de título de la carrera **Técnico de Nivel Superior en Análisis y Programación Computacional** del Instituto Profesional IACC.

Su objetivo es modernizar la operación de estacionamientos mediante la automatización de procesos críticos, tales como:

- Registro de ingresos y salidas de vehículos
- Cálculo automático de tarifas (por minuto, tramos o mensualidad)
- Emisión de tickets en formato PDF
- Generación de reportes filtrables
- Control de usuarios con roles (administrador / operador)
- Registro de asistencias de personal
- Gestión de cierres diarios y mensuales

---

## Características Principales

- Interfaz gráfica intuitiva (GUI)
- Sistema multiusuario con control de roles
- Generación automática de tickets térmicos
- Reportes exportables a PDF
- Configuración flexible de tarifas
- Compatibilidad con impresoras térmicas
- Funcionamiento completamente local (offline)

---

## Tecnologías Utilizadas

- **Lenguaje principal**: Python 3.11+
- **Interfaz gráfica**: PySide6 (Qt para Python)
- **Base de datos**: MySQL
- **Conexión a BD**: `mysql-connector-python`
- **Generación de PDF**: FPDF
- **Estilos visuales**: QSS (Qt Style Sheets)
- **Control de versiones**: Git & GitHub

---

## Requisitos del Sistema

### Hardware
- Procesador de 2 GHz o superior
- Memoria RAM mínima de 4 GB
- Espacio en disco: al menos 1 GB

### Software
- Sistema operativo Windows 10 o superior
- Permisos de administrador
- Impresora térmica instalada (opcional pero recomendada)
- SumatraPDF (para impresión de tickets)

> El sistema no requiere instalación manual de Python ni MySQL.

---

## Instalación Paso a Paso

### 1. Requisitos previos

Verificar que el equipo cumpla con los requisitos indicados anteriormente.

---

### 2. Descarga del instalador

- Instalador:
  (https://www.mediafire.com/file/saweh85twev51wz/Instalador_EstacionamientoCentral_1.1.4.exe/file)

- Repositorio del proyecto:
  (https://github.com/matiasrmb/estacionamiento-central)
> Nota: Es posible que Windows o el antivirus muestren advertencias de seguridad debido a la naturaleza del instalador.

En ese caso:

- Desactivar temporalmente la protección en tiempo real
- Ejecutar el instalador como administrador

---

### 3. Ejecución del instalador

1. Ubicar el archivo `.exe`
2. Clic derecho → **Ejecutar como administrador**
3. Seguir las instrucciones del asistente

---

### 4. Proceso automático de instalación

El instalador realiza las siguientes acciones:

#### 4.1 Copia de archivos

Instala el sistema en:


C:\EstacionamientoCentral


Incluye:

- Ejecutable del sistema
- Archivos de configuración
- Base de datos
- Carpetas de almacenamiento (tickets y reportes)

---

#### 4.2 Configuración de MySQL

- Si no existe → se instala automáticamente
- Si existe → se reutiliza la instalación

Se configura el servicio **MySQL80**.

---

#### 4.3 Creación de base de datos

Base de datos:


estacionamiento_db


- Se crea automáticamente si no existe
- Si existe, se mantiene la información

---

#### 4.4 Usuario de aplicación

Credenciales internas:

- Usuario: `estacionamiento_app`
- Contraseña: `ec_app_2026`

---

#### 4.5 Archivo de configuración

Ruta:


C:\EstacionamientoCentral_internal\config.ini


---

#### 4.6 Instalación de visor PDF

Descargar manualmente:

https://www.sumatrapdfreader.org/download-free-pdf-viewer  

---

#### 4.7 Accesos directos

- Menú inicio
- Escritorio (opcional)

---

### 5. Finalización

El instalador permite ejecutar el sistema inmediatamente al finalizar.

---

## Uso del Sistema

### Flujo básico de operación

1. Iniciar sesión (administrador u operador)
2. Acceder al panel principal
3. Ejecutar acciones:

- Registrar ingreso de vehículo
- Registrar salida (cálculo automático)
- Visualizar vehículos activos
- Generar reportes
- Realizar cierres
- Administrar usuarios
- Configurar tarifas

---

## Arquitectura del Sistema

El sistema sigue una arquitectura modular basada en el patrón **MVC (Modelo-Vista-Controlador)**:

- **Views** → Interfaz gráfica (PySide6)
- **Controllers** → Lógica de negocio
- **Utils** → Funciones auxiliares (PDF, DB, etc.)
- **MySQL** → Persistencia de datos

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


## Créditos

- Desarrollador principal: Matías Román Medina Becerra
- Institución: Instituto Profesional IACC
- Proyecto de Título: Técnico de Nivel Superior en Análisis y Programación Computacional
- Año: 2025
