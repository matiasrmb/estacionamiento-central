# styles.py
"""
Hoja de estilos global para Estacionamiento Central (Qt StyleSheet / QSS).

La idea es:
- Unificar tipografía, colores y bordes.
- Dar un look consistente a botones, inputs, tablas y groupboxes.
"""

GLOBAL_STYLESHEET = """
/* ================== BASE ================== */

* {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}

/* Fondo general de las ventanas */
QWidget {
    background-color: #f3f4f6;
    color: #111827;
}

/* Labels principales (títulos dentro de ventanas) */
QLabel#TituloVentana {
    font-size: 16px;
    font-weight: bold;
}

/* ================== BOTONES ================== */

QPushButton {
    background-color: #2563eb;          /* azul */
    color: white;
    border-radius: 6px;
    padding: 6px 10px;
    border: 1px solid #1d4ed8;
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

/* Botones "secundarios" (por ejemplo, enlaces o acciones menos críticas) */
QPushButton#BotonSecundario {
    background-color: transparent;
    color: #2563eb;
    border: none;
    padding: 2px 4px;
    text-align: left;
}

QPushButton#BotonSecundario:hover {
    text-decoration: underline;
}

/* ================== INPUTS ================== */

QLineEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: white;
    border-radius: 4px;
    border: 1px solid #d1d5db;
    padding: 4px 6px;
}

QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

/* Placeholder más suave */
QLineEdit[echoMode="0"]::placeholder { 
    color: #9ca3af;
}

/* ================== GROUPBOX ================== */

QGroupBox {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #374151;
    font-weight: bold;
}

/* ================== TABLAS ================== */

QTableWidget {
    background-color: #ffffff;
    gridline-color: #e5e7eb;
    border-radius: 4px;
    border: 1px solid #d1d5db;
}

QHeaderView::section {
    background-color: #e5e7eb;
    padding: 4px;
    border: none;
    border-right: 1px solid #d1d5db;
    font-weight: bold;
}

QTableWidget::item {
    padding: 2px 4px;
}

/* Alternar color de filas */
QTableView {
    alternate-background-color: #f9fafb;
}

/* ================== SCROLLBARS ================== */

QScrollBar:vertical {
    background: #f3f4f6;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #9ca3af;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ================== MENSAJES ================== */

QMessageBox {
    background-color: #ffffff;
}

/* ================== CAMPOS ESPECÍFICOS ================== */

/* Por si quieres un input de patente con estilo ligeramente distinto */
QLineEdit#InputPatente {
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}
"""
