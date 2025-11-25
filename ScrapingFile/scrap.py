import sys, requests
from bs4 import BeautifulSoup

try:
    src, eid = sys.argv[1], sys.argv[2]
    html = requests.get(src).text if src.startswith("http") else open(src, encoding="utf-8").read()
    print(BeautifulSoup(html, "html.parser").find(id=eid).get_text(strip=True))

except IndexError:
    print("Uso: python script.py <URL_O_ARCHIVO> <ID>")
except AttributeError:
    print(f"Error: No se encontró ningún elemento con id='{eid}'")
except Exception as e:
    print(f"Error general: {e}")