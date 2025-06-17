from controllers.tarifas_controller import calcular_tarifa

# Lista de minutos a probar
minutos_de_prueba = [14, 21, 26, 30, 32, 37, 41, 46, 50, 55, 60, 61, 74, 83, 115, 143, 180]

print("🔎 Prueba de cálculo de tarifas:")
for minutos in minutos_de_prueba:
    tarifa = calcular_tarifa(minutos)
    print(f"{minutos} minutos -> ${tarifa}")
