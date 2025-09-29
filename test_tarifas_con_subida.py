from datetime import datetime, timedelta
from controllers.tarifas_controller import calcular_tarifa

# 🔧 Monkeypatch para aislar de la base de datos
import controllers.tarifas_controller as tc

# Configuración base
tc.obtener_configuracion = lambda: {
    "modo_cobro": "personalizado",
    "tarifa_minima": "300",
    "tarifa_hora": "1300"
}

# Tramos base en memoria
tc.obtener_tarifas_personalizadas = lambda: [
    {"minuto_inicio": 0, "minuto_fin": 14, "valor": 300},
    {"minuto_inicio": 15, "minuto_fin": 21, "valor": 400},
    {"minuto_inicio": 22, "minuto_fin": 26, "valor": 500},
    {"minuto_inicio": 27, "minuto_fin": 30, "valor": 600},
    {"minuto_inicio": 31, "minuto_fin": 32, "valor": 700},
    {"minuto_inicio": 33, "minuto_fin": 37, "valor": 800},
    {"minuto_inicio": 38, "minuto_fin": 41, "valor": 900},
    {"minuto_inicio": 42, "minuto_fin": 46, "valor": 1000},
    {"minuto_inicio": 47, "minuto_fin": 50, "valor": 1100},
    {"minuto_inicio": 51, "minuto_fin": 55, "valor": 1200},
    {"minuto_inicio": 56, "minuto_fin": 60, "valor": 1300},
]

def simular_subida(monto_extra):
    """
    Configura una subida activa en memoria, desde hace 1h hasta dentro de 1h.
    """
    ahora = datetime.now()
    hora_inicio = (ahora - timedelta(hours=1)).strftime("%H:%M:%S")
    hora_fin = (ahora + timedelta(hours=1)).strftime("%H:%M:%S")
    tc.obtener_subida_activa = lambda: {
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "monto_adicional": monto_extra
    }

def probar_interactivo():
    print("=== PRUEBA DE TARIFAS CON SUBIDA SIMULADA ===")
    print("Tramos definidos en memoria:")
    for t in tc.obtener_tarifas_personalizadas():
        print(f"  {t['minuto_inicio']:02}-{t['minuto_fin']:02} min → ${t['valor']}")
    print("")

    monto_extra = 0
    simular_subida(monto_extra)

    while True:
        entrada = input("⏱ Ingresa minutos (o 'q' para salir, 'm' para cambiar monto subida): ").strip().lower()
        if entrada == "q":
            print("👋 Saliendo de pruebas...")
            break
        if entrada == "m":
            nuevo_monto = input("💲 Ingresa nuevo monto extra (+100, +200, etc): ").strip()
            if nuevo_monto.isdigit():
                monto_extra = int(nuevo_monto)
                simular_subida(monto_extra)
                print(f"✅ Subida actualizada a +${monto_extra}\n")
            else:
                print("❌ Monto inválido, usa un número entero.")
            continue
        if not entrada.isdigit():
            print("❌ Ingresa un número válido.")
            continue

        minutos = int(entrada)
        total, subida_aplicada, monto = calcular_tarifa(minutos, datetime.now(), datetime.now(), devolver_flag=True)
        print(f"➡ {minutos} min → ${total} {'(con subida)' if subida_aplicada else '(sin subida)'} (+${monto} por tramo)\n")

if __name__ == "__main__":
    probar_interactivo()
