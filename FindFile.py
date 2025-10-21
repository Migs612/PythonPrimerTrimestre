import sys

def buscar_texto(filename, search):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            count = content.count(search)
            print(f"{search}: {count}")
    except FileNotFoundError:
        print("Archivo no encontrado.")
    except Exception as e:
        print(f"Error: {e}")

if len(sys.argv) == 3:
    buscar_texto(sys.argv[1], sys.argv[2])
else:
    print("Uso: python FindFile.py <archivo> <texto>")
