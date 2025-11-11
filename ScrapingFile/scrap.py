from __future__ import annotations

import argparse
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_URL = "http://127.0.0.1:5500/ScrapingFile/index.html"


class ScraperError(Exception):
    pass


def fetch_url(url: str, timeout: int = 5) -> str:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as exc:
        raise ScraperError(f"Error al conectar con {url}: {exc}") from exc


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as exc:
        raise ScraperError(f"No se pudo leer el archivo '{path}': {exc}") from exc


def parse_and_extract(html: str, element_id: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    target = soup.find(id=element_id)
    if target is None:
        alt = soup.select(f"[id*='{element_id}']")
        if alt:
            target = alt[0]
        else:
            raise ScraperError(f"Elemento con id '{element_id}' no encontrado en el documento.")
    text = target.get_text(separator=" ", strip=True)
    return text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scraper local para extraer un elemento por id desde Live Server o archivo local")
    p.add_argument("--url", help="URL de la página local (ej. http://127.0.0.1:5500/index.html)", default=DEFAULT_URL)
    p.add_argument("--file", help="Archivo HTML local como fallback (path relativo o absoluto)", default=None)
    p.add_argument("--id", help="ID del elemento a extraer", default="featured-animal")
    p.add_argument("--timeout", type=int, default=5, help="Timeout en segundos para la petición HTTP")
    p.add_argument("--verbose", action="store_true", help="Mostrar mensajes detallados de depuración")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    html: Optional[str] = None

    try:
        if args.verbose:
            print(f"[DEBUG] Intentando descargar desde URL: {args.url}")
        html = fetch_url(args.url, timeout=args.timeout)
    except ScraperError as e:
        print(f"Advertencia: {e}")
        if args.file:
            if args.verbose:
                print(f"[DEBUG] Intentando fallback leyendo el archivo local: {args.file}")
            try:
                html = read_file(args.file)
            except ScraperError as e2:
                print(f"Error al leer archivo local: {e2}")
                return 2
        else:
            print("No se pudo conectar a la URL y no se proporcionó --file. Activa Live Server o pasa la opción --file.")
            return 1

    try:
        value = parse_and_extract(html, args.id)
        print("\nValor encontrado:")
        print(value)
        return 0
    except ScraperError as e:
        print(f"Error al extraer el elemento: {e}")
        return 3
    except Exception as e:
        print(f"Error inesperado: {e}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
