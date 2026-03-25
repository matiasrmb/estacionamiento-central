
GLOBAL_STYLESHEET = """
/* =========================================================
   BASE
   ========================================================= */

* {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: #f3f4f6;
    color: #111827;
}

/* =========================================================
   TIPOGRAFÍA
   ========================================================= */

QLabel#TituloVentana {
    font-size: 22px;
    font-weight: 700;
    padding: 4px 0 6px 0;
    color: #111827;
}

QLabel#SubtituloSeccion {
    font-size: 14px;
    color: #6b7280;
    padding-bottom: 2px;
}

QLabel#EtiquetaFormulario {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
}

QLabel#TituloPanelOperativo {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}

QLabel#TituloResumenModulo {
    font-size: 13px;
    color: #6b7280;
}

QLabel#ValorResumenModulo {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}

QLabel#TituloAcceso {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
}

QLabel#SubtituloAcceso {
    font-size: 13px;
    color: #6b7280;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

QFrame#Sidebar {
    background-color: #111827;
    border-right: 1px solid #1f2937;
}

QFrame#Sidebar QLabel {
    background: transparent;
    color: #f9fafb;
}

QFrame#Sidebar QLabel#TituloVentana {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
    padding: 4px 6px;
}

QFrame#Sidebar QLabel#SubtituloSeccion {
    color: #cbd5e1;
    font-size: 13px;
}

QFrame#Sidebar QPushButton {
    background-color: #1f2937;
    color: #f9fafb;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    min-height: 20px;
}

QFrame#Sidebar QPushButton:hover {
    background-color: #2563eb;
    border-color: #2563eb;
}

QFrame#Sidebar QPushButton:pressed {
    background-color: #1d4ed8;
}

QFrame#Sidebar QPushButton#BotonPeligro {
    background-color: #7f1d1d;
    border-color: #991b1b;
    color: #ffffff;
}

QFrame#Sidebar QPushButton#BotonPeligro:hover {
    background-color: #b91c1c;
}

/* =========================================================
   BOTONES
   ========================================================= */

QPushButton {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 8px 12px;
    border: 1px solid #1d4ed8;
    font-weight: 600;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #9ca3af;
    border-color: #6b7280;
    color: #e5e7eb;
}

QPushButton#BotonSecundario {
    background-color: #ffffff;
    color: #2563eb;
    border: 1px solid #cbd5e1;
    text-align: center;
}

QPushButton#BotonSecundario:hover {
    background-color: #eff6ff;
    border-color: #93c5fd;
}

QPushButton#BotonPeligro {
    background-color: #dc2626;
    border-color: #b91c1c;
    color: #f9fafb;
}

QPushButton#BotonPeligro:hover {
    background-color: #b91c1c;
}

QPushButton#BotonPeligro:pressed {
    background-color: #991b1b;
}

/* Botones compactos dentro de tablas */
QPushButton#BotonTabla {
    padding: 6px 10px;
    font-size: 12px;
    min-height: 28px;
    border-radius: 6px;
}

QPushButton#BotonTablaPeligro {
    background-color: #dc2626;
    border-color: #b91c1c;
    color: #f9fafb;
    padding: 6px 10px;
    font-size: 12px;
    min-height: 28px;
    border-radius: 6px;
}

QPushButton#BotonTablaPeligro:hover {
    background-color: #b91c1c;
}

/* =========================================================
   INPUTS
   ========================================================= */

QLineEdit, QPlainTextEdit, QSpinBox, QComboBox, QDateEdit, QTimeEdit {
    background-color: white;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    padding: 8px 10px;
    min-height: 22px;
}

QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 1px solid #2563eb;
}

QLineEdit#InputPatente {
    font-weight: bold;
    letter-spacing: 1px;
}

/* =========================================================
   GROUPBOX / PANELES
   ========================================================= */

QGroupBox {
    border: 1px solid #d1d5db;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #374151;
    font-weight: 700;
}

/* Tarjetas resumen principales */
QFrame#TarjetaResumen {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 12px;
}

/* Tarjetas resumen modulares */
QFrame#ResumenModulo {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 12px;
}

QFrame#ResumenModulo QLabel {
    background-color: transparent;
    color: #111827;
}

/* Paneles tipo tarjeta */
QFrame#PanelFormulario {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 12px;
}

/* Panel de acceso/login/setup */
QFrame#CardAcceso {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 14px;
}

/* =========================================================
   TABLAS
   ========================================================= */

QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #f9fafb;
    gridline-color: #e5e7eb;
    border-radius: 10px;
    border: 1px solid #d1d5db;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}

QHeaderView::section {
    background-color: #e5e7eb;
    padding: 8px;
    border: none;
    border-right: 1px solid #d1d5db;
    font-weight: 700;
}

QTableWidget::item {
    padding: 6px 8px;
}

/* Tabla especial de activos */
QTableWidget#TablaActivos {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #e5e7eb;
    border-radius: 10px;
    border: 1px solid #d1d5db;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}

QTableWidget#TablaActivos::item {
    padding: 8px 10px;
}

QLabel#LeyendaTabla {
    color: #6b7280;
    font-size: 12px;
    padding-top: 4px;
}

/* =========================================================
   SCROLLBARS
   ========================================================= */

QScrollBar:vertical {
    background: #f3f4f6;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #9ca3af;
    min-height: 24px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* =========================================================
   ESTADOS / MENSAJES
   ========================================================= */

QMessageBox {
    background-color: #ffffff;
}

QLabel#EstadoInfo {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 12px;
    color: #1e3a8a;
    font-size: 13px;
}

QLabel#EstadoInfoNeutro {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 12px;
    color: #1e3a8a;
    font-size: 13px;
}

QLabel#EstadoInfoOk {
    background-color: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    padding: 10px 12px;
    color: #065f46;
    font-size: 13px;
}

QLabel#EstadoInfoWarn {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 10px 12px;
    color: #92400e;
    font-size: 13px;
}

QLabel#EstadoInfoError {
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 10px 12px;
    color: #991b1b;
    font-size: 13px;
}

QLabel#EstadoSubidaActiva {
    background-color: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 8px;
    padding: 10px 12px;
    color: #9a3412;
    font-size: 13px;
    font-weight: 600;
}

QLabel#EstadoSubidaInactiva {
    background-color: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 10px 12px;
    color: #4b5563;
    font-size: 13px;
}

/* =========================================================
   PANEL OPERATIVO
   ========================================================= */

QFrame#PanelOperativo {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 12px;
}

QFrame#PanelOperativo QLabel {
    color: #111827;
    background-color: transparent;
}

QFrame#PanelOperativo QLabel#TituloPanelOperativo {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}

QFrame#PanelOperativo QLabel#EstadoOperativoOk {
    background-color: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    padding: 8px 10px;
    color: #065f46;
    font-size: 12px;
    font-weight: 600;
}

QFrame#PanelOperativo QLabel#EstadoOperativoWarn {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 8px 10px;
    color: #92400e;
    font-size: 12px;
    font-weight: 600;
}

QFrame#PanelOperativo QLabel#EstadoOperativoNeutro {
    background-color: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 10px;
    color: #4b5563;
    font-size: 12px;
    font-weight: 600;
}
"""