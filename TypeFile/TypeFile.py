# Autor: Manuel Gutierrez @migs612
import sys


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) != 2:
        print("Uso: python TypeFile.py <archivo>")
        return 1

    filename = argv[1]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                print(f"{i:04d}: {line.rstrip()}")
    except FileNotFoundError:
        print(f"Error: el archivo '{filename}' no existe.")
        return 2
    except Exception as e:
        print(f"Se produjo un error al leer el archivo: {e}")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
