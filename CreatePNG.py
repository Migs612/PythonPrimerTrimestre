# Manuel Gutierrez @migs612
import sys
import os
import random
import string
import uuid

def random_name(length=15):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def crear_pngs(folder, n):
    # Crear carpeta si no existe
    os.makedirs(folder, exist_ok=True)

    try:
        existing = set(os.path.normcase(f) for f in os.listdir(folder))
    except FileNotFoundError:
        existing = set()

    created = 0
    for _ in range(n):
        attempts = 0
        while True:
            name = random_name() + ".png"
            norm_name = os.path.normcase(name)

            if norm_name in existing:
                attempts += 1
                if attempts >= 100:
                    name = uuid.uuid4().hex + ".png"
                    norm_name = os.path.normcase(name)
                    if norm_name in existing:
                        continue
                else:
                    continue

            path = os.path.join(folder, name)
            try:
                with open(path, 'xb') as f:
                    f.write(b'')
                existing.add(norm_name)
                created += 1
                break
            except FileExistsError:
                existing.add(os.path.normcase(os.path.basename(path)))
                attempts += 1
                if attempts >= 1000:
                    raise Exception("No se pudo generar un nombre de archivo único después de muchos intentos")

    print(f"Se crearon {created} archivos PNG en la carpeta '{folder}'.")

if len(sys.argv) == 3:
    try:
        folder = sys.argv[1]
        n = int(sys.argv[2])
        crear_pngs(folder, n)
    except ValueError:
        print("La cantidad debe ser un número entero.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Uso: python CreatePNG.py <carpeta> <cantidad>")
