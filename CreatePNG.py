import sys
import os
import random
import string

def random_name(length=15):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def crear_pngs(folder, n):
    os.makedirs(folder, exist_ok=True)
    for _ in range(n):
        name = random_name() + ".png"
        path = os.path.join(folder, name)
        with open(path, 'wb') as f:
            f.write(b'')
    print(f"Se crearon {n} archivos PNG en la carpeta '{folder}'.")

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
