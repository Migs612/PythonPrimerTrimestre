# Manuel Gutierrez @migs612
import sys
import os
import random
import string


def nombre_aleatorio(longitud=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=longitud))


def crear_pngs(cantidad, carpeta="img"):
    os.makedirs(carpeta, exist_ok=True)

    try:
        existentes = set(os.path.normcase(f) for f in os.listdir(carpeta))
    except Exception:
        existentes = set()

    creados = 0

    while creados < cantidad:
        nombre = nombre_aleatorio() + ".png"
        nombre_norm = os.path.normcase(nombre)

        if nombre_norm in existentes:
            continue

        ruta = os.path.join(carpeta, nombre)
        try:
            with open(ruta, "xb"):
                pass
            existentes.add(nombre_norm)
            creados += 1
        except FileExistsError:
            existentes.add(os.path.normcase(os.path.basename(ruta)))
            continue

    return creados


def main(argumentos=None):
    if argumentos is None:
        argumentos = sys.argv

    if len(argumentos) < 2:
        print("Uso: python CreatePNG.py <cantidad_de_archivos> [carpeta]")
        return 1

    try:
        cantidad = int(argumentos[1])
        if cantidad < 0:
            print("La cantidad debe ser un número entero no negativo.")
            return 1
    except ValueError:
        print("La cantidad debe ser un número entero.")
        return 1

    carpeta = argumentos[2] if len(argumentos) >= 3 else "img"

    try:
        creados = crear_pngs(cantidad, carpeta)
        print(f"Se crearon {creados} archivos PNG en la carpeta '{carpeta}'.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
