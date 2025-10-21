import sys

def mostrar_archivo(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                print(f"{i}: {line.rstrip()}")
    except FileNotFoundError:
        print("Archivo no encontrado.")
    except Exception as e:
        print(f"Error: {e}")

if len(sys.argv) == 2:
    mostrar_archivo(sys.argv[1])
else:
    print("Uso: python TypeFile.py <archivo>")
