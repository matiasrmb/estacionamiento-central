-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS estacionamiento_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE estacionamiento_db;

-- Tabla de vehículos
CREATE TABLE IF NOT EXISTS vehiculos (
    id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    patente VARCHAR(10) NOT NULL UNIQUE,
    tipo_cliente ENUM('ocasional', 'mensual') NOT NULL DEFAULT 'ocasional',
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de ingresos/salidas
CREATE TABLE IF NOT EXISTS ingresos (
    id_ingreso INT AUTO_INCREMENT PRIMARY KEY,
    id_vehiculo INT NOT NULL,
    fecha_hora_ingreso DATETIME NOT NULL,
    fecha_hora_salida DATETIME DEFAULT NULL,
    tarifa_aplicada DECIMAL(10,2) DEFAULT NULL,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo)
);

-- Tabla de usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave_hash VARCHAR(255) NOT NULL,
    rol ENUM('administrador', 'operador') NOT NULL
);

-- Tabla de configuración (para tarifas y otros parámetros)
CREATE TABLE IF NOT EXISTS configuracion (
    clave VARCHAR(50) PRIMARY KEY,
    valor VARCHAR(255) NOT NULL
);
