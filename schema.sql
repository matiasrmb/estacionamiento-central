-- Crear base de datos
CREATE DATABASE IF NOT EXISTS estacionamiento_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE estacionamiento_db;

-- Tabla de usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave_hash VARCHAR(255) NOT NULL,
    rol ENUM('administrador', 'operador') NOT NULL,
    activo TINYINT(1) DEFAULT 1
);

-- Tabla de vehículos
CREATE TABLE IF NOT EXISTS vehiculos (
    id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    patente VARCHAR(10) NOT NULL UNIQUE,
    tipo_cliente ENUM('ocasional', 'mensual') NOT NULL DEFAULT 'ocasional',
    activo TINYINT(1) DEFAULT 1,
    tarifa_mensual DECIMAL(10,2) DEFAULT NULL
);

-- Tabla de ingresos
CREATE TABLE IF NOT EXISTS ingresos (
    id_ingreso INT AUTO_INCREMENT PRIMARY KEY,
    id_vehiculo INT NOT NULL,
    fecha_hora_ingreso DATETIME NOT NULL,
    fecha_hora_salida DATETIME DEFAULT NULL,
    tarifa_aplicada DECIMAL(10,2) DEFAULT NULL,
    en_espera TINYINT(1) DEFAULT 0,
    cerrado TINYINT(1) DEFAULT 0,
    reingresado TINYINT(1) DEFAULT 0,
    usuario VARCHAR(50),
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo)
);

-- Tabla de configuración del sistema (clave/valor)
CREATE TABLE IF NOT EXISTS configuracion (
    clave VARCHAR(50) PRIMARY KEY,
    valor VARCHAR(255) NOT NULL
);

-- Tabla de tarifas personalizadas
CREATE TABLE IF NOT EXISTS tarifas_personalizadas (
    id_tarifa INT AUTO_INCREMENT PRIMARY KEY,
    minuto_inicio INT NOT NULL,
    minuto_fin INT NOT NULL,
    valor INT NOT NULL
);

-- Tabla de usos de baño
CREATE TABLE IF NOT EXISTS usos_bano (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME NOT NULL,
    monto INT NOT NULL,
    usuario VARCHAR(50) NOT NULL
);

-- Tabla de cierres diarios
CREATE TABLE IF NOT EXISTS cierres_diarios (
    id_cierre INT AUTO_INCREMENT PRIMARY KEY,
    fecha_inicio DATETIME NOT NULL,
    fecha_cierre DATETIME NOT NULL,
    total_recaudado INT NOT NULL,
    total_ingresos INT NOT NULL,
    total_salidas INT NOT NULL,
    total_banos INT DEFAULT 0,
    total_banos_monto INT DEFAULT 0,
    usuario VARCHAR(50) NOT NULL
);

-- Tabla de asistencias (registro de sesiones de usuarios)
CREATE TABLE IF NOT EXISTS asistencias (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    hora_inicio DATETIME NOT NULL,
    hora_salida DATETIME DEFAULT NULL,
    cantidad_movimientos INT DEFAULT 0,
    total_recaudado DECIMAL(10,2) DEFAULT 0
);

-- Inserción inicial de configuración
INSERT INTO configuracion (clave, valor) VALUES
('modo_cobro', 'minuto'),
('tarifa_minima', '300'),
('tarifa_hora', '1300'),
('modo_auto_simplificado', '0')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);
