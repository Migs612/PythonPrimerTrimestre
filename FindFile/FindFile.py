# Manuel Gutierrez @migs612
import sys
import os


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) != 3:
        print(f"Uso: python FindFile.py <archivo> <texto>")
        return 1
    filename, search = argv[1], argv[2]
    try:
        if not os.path.exists(filename):
            print(f"Error: el archivo '{filename}' no existe.")
            return 2
        with open(filename, "r", encoding="utf-8") as f:
            count = f.read().count(search)
        print(f"{search} : {count}")
        return 0
    except Exception:
        print("Se produjo un error al leer el archivo.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
