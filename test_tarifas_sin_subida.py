from datetime import datetime
from controllers.tarifas_controller import calcular_tarifa

# 🔧 Monkeypatch manual para que no dependa de la base de datos
import controllers.tarifas_controller as tc

tc.obtener_configuracion = lambda: {
    "modo_cobro": "personalizado",
    "tarifa_minima": "300",
    "tarifa_hora": "1300"
}

tc.obtener_tarifas_personalizadas = lambda: [
    {"minuto_inicio": 0, "minuto_fin": 15, "valor": 300},
    {"minuto_inicio": 16, "minuto_fin": 21, "valor": 400},
    {"minuto_inicio": 22, "minuto_fin": 27, "valor": 500},
    {"minuto_inicio": 28, "minuto_fin": 30, "valor": 600},
    {"minuto_inicio": 31, "minuto_fin": 32, "valor": 700},
    {"minuto_inicio": 33, "minuto_fin": 36, "valor": 800},
    {"minuto_inicio": 37, "minuto_fin": 41, "valor": 900},
    {"minuto_inicio": 42, "minuto_fin": 47, "valor": 1000},
    {"minuto_inicio": 48, "minuto_fin": 52, "valor": 1100},
    {"minuto_inicio": 53, "minuto_fin": 57, "valor": 1200},
    {"minuto_inicio": 58, "minuto_fin": 59, "valor": 1300},
]

tc.obtener_subida_activa = lambda: None  # Sin subida para esta prueba

def probar_interactivo():
    print("=== PRUEBA DIRECTA DE TARIFAS ===")
    print("Tramos definidos en memoria:")
    for t in tc.obtener_tarifas_personalizadas():
        print(f"  {t['minuto_inicio']:02}-{t['minuto_fin']:02} min → ${t['valor']}")
    print("")

    while True:
        entrada = input("⏱ Ingresa minutos (o 'q' para salir): ").strip().lower()
        if entrada == "q":
            print("👋 Saliendo de pruebas...")
            break
        if not entrada.isdigit():
            print("❌ Ingresa un número válido.")
            continue

        minutos = int(entrada)
        total = calcular_tarifa(minutos)
        print(f"➡ {minutos} min → ${total}\n")

if __name__ == "__main__":
    probar_interactivo()
