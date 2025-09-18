from controllers.cierres_controller import realizar_cierre_mensual
from datetime import datetime

# 👇 Prueba: intentar cerrar el mes actual en un día NO permitido
print("1. Cerrando mes actual en un día no final:")
fecha_prueba_1 = datetime(2025, 8, 15)  # 15 de agosto (NO válido para cerrar agosto)
exito, mensaje = realizar_cierre_mensual("admin", fecha_prueba_1)
print(f"Resultado: {mensaje}\n")

# 👇 Prueba: cerrar mes anterior durante el mes siguiente (válido)
print("2. Cerrando julio durante agosto:")
fecha_prueba_2 = datetime(2025, 8, 5)
exito, mensaje = realizar_cierre_mensual("admin", fecha_prueba_2)
print(f"Resultado: {mensaje}\n")

# 👇 Prueba: intentar cerrar un mes con más de un mes de atraso (NO permitido)
print("3. Intentar cerrar junio en agosto:")
fecha_prueba_3 = datetime(2025, 8, 5)
# Para probar esto debes tener ingresos de junio no cerrados
exito, mensaje = realizar_cierre_mensual("admin", fecha_prueba_3)
print(f"Resultado: {mensaje}\n")

# 👇 Prueba: cerrar agosto en el día final (válido)
print("4. Cerrando agosto el 31:")
fecha_prueba_4 = datetime(2025, 8, 31)
exito, mensaje = realizar_cierre_mensual("admin", fecha_prueba_4)
print(f"Resultado: {mensaje}\n")
