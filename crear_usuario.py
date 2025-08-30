import argparse
from controllers.usuarios_controller import crear_usuario

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear un nuevo usuario.")
    parser.add_argument("usuario", help="Nombre de usuario")
    parser.add_argument("clave", help="Contraseña del usuario")
    parser.add_argument("rol", choices=["operador", "administrador"], help="Rol del usuario")

    args = parser.parse_args()

    try:
        crear_usuario(args.usuario, args.clave, args.rol)
        print(f"Usuario '{args.usuario}' creado exitosamente con rol '{args.rol}'.")
    except Exception as e:
        print(f"Error al crear el usuario: {e}")