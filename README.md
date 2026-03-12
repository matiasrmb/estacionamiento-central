
# Estacionamiento Central

**Estacionamiento Central** es una aplicación de escritorio para Windows que permite gestionar de forma eficiente un estacionamiento con entradas/salidas de vehículos, cobros automáticos, generación de tickets, reportes y cierres diarios. Está diseñada para equipos con recursos limitados y es compatible con impresoras térmicas Bluetooth de 58mm.


## Descripción

Este software fue desarrollado como parte del proyecto de título técnico en análisis y programación computacional de IACC. El objetivo es modernizar la gestión de estacionamientos optimizando el registro de vehículos, cálculo de tarifas y control administrativo, incluyendo:

- Registro de ingresos y salidas
- Cálculo automático de tarifas por minuto, tramo o mensualidad
- Emisión de tickets térmicos
- Generación de reportes filtrables en PDF
- Control de usuarios (operador, administrador)
- Asistencias de personal
- Cierres diarios y mensuales
## Tecnologías Utilizadas

- **Lenguaje principal**: Python 3.11+
- **Interfaz gráfica**: PySide6 (Qt para Python)
- **Base de datos**: MySQL
- **ORM/Conexión**: `mysql-connector-python`
- **Estilo PDF**: FPDF
- **Estilos visuales**: QSS (Qt Style Sheets)
- **Control de versiones**: Git & GitHub


## Requisitos del Sistema

- Sistema Operativo: Windows 10 u 11
- Python 3.11 o superior
- MySQL Server (local o remoto)
- Visual Studio Code (recomendado para desarrollo)
- Sumatra PDF (para impresión directa)
- Impresora térmica de 58mm (opcional)
## Instalación Paso a Paso


### 1. Clonar repositorio

```bash
git clone https://github.com/tu_usuario/estacionamiento-central.git
cd estacionamiento-central
```

### 2. Crear entorno viertual (opcional pero recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear archivo de configuración de base de datos

```ini
[mysql]
host = localhost
port = 3306
user = tu_usuario
password = tu_contraseña
database = estacionamiento_db
```

### 5.Crear base de datos y tablas

Puedes ejecutar el script SQL incluido 'schema.sql'


## Uso del Sistema

### 1. Ejecutar el archivo principal:

```bash
python main.py
```


### 2. Iniciar sesión como operador o administrador.

### 3. Acceder a las siguientes funcionalidades desde el panel principal:

- Ingresar vehículos (y emitir ticket)
- Registrar salida (y emitir ticket con cálculo)
- Ver vehículos activos
- Generar reportes de ingresos/salidas
- Generar reportes de asistencias
- Realizar cierres diarios o mensuales
- Administrar usuarios
- Cambiar configuración del sistema
## Estructura del Proyecto

```graphql
estacionamiento-central/
│
├── controllers/          # Lógica del sistema (negocio, reglas)
│   ├── usuarios_controller.py
│   ├── registro_controller.py
│   └── ...
│
├── utils/                # Funciones auxiliares y comunes
│   ├── db.py
│   ├── ticket.py
│   └── pdf_utils.py
│
├── views/                # Interfaces gráficas con PySide6
│   ├── login.py
│   ├── ingreso.py
│   └── ...
│
├── assets/               # Imágenes, íconos o capturas del sistema
│
├── styles/               # Archivos QSS para estilos personalizados
│   └── estilos.qss
│
├── tickets/              # Tickets térmicos generados en PDF
├── reportes/             # Reportes PDF filtrados por fecha y patente
├── asistencias/          # Reportes PDF de asistencias de usuario
├── cierres/              # Cierres diarios o mensuales (PDF)
│
├── config.ini            # Archivo de configuración de base de datos
├── main.py               # Punto de entrada al sistema
└── README.md             # Este archivo

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
