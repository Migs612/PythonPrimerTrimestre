import re
import glob
import subprocess
from datetime import datetime
from pathlib import Path

class IdRegistry:
    def __init__(self):
        self.catalogos = {'sucursal': {}, 'empleado': {}, 'producto': {}}
        self.contadores = {k: 1 for k in self.catalogos}
        self.seq_ticket = 1
        self.seq_linea = 1
        self.seq_pago = 1

    def obtener_id(self, tipo, clave, datos_extra=None):
        if clave not in self.catalogos[tipo]:
            self.catalogos[tipo][clave] = {
                'id': self.contadores[tipo],
                'datos': datos_extra or {}
            }
            self.contadores[tipo] += 1
        return self.catalogos[tipo][clave]['id']

def parsear_factura(ruta_archivo, registro):
    try:
        texto = ruta_archivo.read_text(encoding='utf-8')
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    except Exception as e:
        print(f"Error leyendo {ruta_archivo.name}: {e}")
        return None

    contenido_completo = "\n".join(lineas)

    nombre_empresa = "SUPERMERCADOS EL AHORRO"
    if "SUPERMERCADOS EL AHORRO" in contenido_completo:
        nombre_empresa = "SUPERMERCADOS EL AHORRO"

    match_dir = re.search(r'(C\.|Calle|Avda).*?(\d+)?.*', contenido_completo, re.IGNORECASE)
    direccion = match_dir.group(0).strip() if match_dir else ""

    match_cif = re.search(r'CIF:\s*([A-Z0-9\-]+)', contenido_completo)
    cif = match_cif.group(1).strip() if match_cif else "00000000T"

    match_fecha = re.search(r'Fecha:\s*(\d{2}/\d{2}/\d{4})', contenido_completo)
    match_hora = re.search(r'Hora:\s*(\d{2}:\d{2})', contenido_completo)
    match_ticket = re.search(r'Ticket:\s*(\d+)', contenido_completo)

    match_cajero = re.search(r'Cajero:\s*(\d+)\s*-\s*(.+)', contenido_completo)

    errores = []
    if not match_fecha: errores.append("Falta Fecha")
    if not match_ticket: errores.append("Falta Nº Ticket")
    
    if errores:
        print(f"{ruta_archivo.name} omitido por: {', '.join(errores)}")
        return None

    sucursal_info = {'nombre': nombre_empresa, 'direccion': direccion, 'cif': cif}
    id_sucursal = registro.obtener_id('sucursal', nombre_empresa, sucursal_info)

    nombre_cajero = match_cajero.group(2).strip() if match_cajero else "Cajero"
    codigo_cajero = match_cajero.group(1).strip() if match_cajero else "999"
    id_empleado = registro.obtener_id('empleado', codigo_cajero, {'nombre': nombre_cajero})

    hora_str = match_hora.group(1) if match_hora else "00:00"
    try:
        dt = datetime.strptime(f"{match_fecha.group(1)} {hora_str}", "%d/%m/%Y %H:%M")
        fecha_sql = dt.strftime("%Y-%m-%d %H:%M:00")
    except:
        fecha_sql = '2025-01-01 00:00:00'

    items_procesados = []
    base_imponible = 0.0

    patron_item = re.compile(r'^\s*(\d+(?:\.\d+)?)\s+(.+?)\s+(\d+\.\d{2})\s*€')

    try:
        idx_inicio = next(i for i, l in enumerate(lineas) if 'DESCRIPCIÓN' in l.upper()) + 1
    except StopIteration:
        idx_inicio = 0

    i = idx_inicio
    while i < len(lineas):
        linea = lineas[i]

        if 'TOTAL' in linea.upper() or 'SUBTOTAL' in linea.upper():
            break
        if 'FORMA DE PAGO' in linea:
            break

        if linea.startswith('---'):
            i += 1
            continue

        if not linea.strip().endswith('€') and (i + 1 < len(lineas)):
            siguiente = lineas[i+1].strip()
            if re.match(r'^\d+\.\d{2}\s*€$', siguiente):
                linea = f"{linea} {siguiente}"
                i += 1

        match = patron_item.match(linea)
        if match:
            cantidad = float(match.group(1))
            descripcion = match.group(2).strip()
            subtotal = float(match.group(3))
            
            id_producto = registro.obtener_id('producto', descripcion, {})
            items_procesados.append((id_producto, cantidad, subtotal))
            base_imponible += subtotal
        
        i += 1

    total_con_iva = round(base_imponible * 1.21, 2)

    match_pago = re.search(r'FORMA DE PAGO:\s*(.+)', contenido_completo)
    metodo_pago = match_pago.group(1).strip() if match_pago else "EFECTIVO"
    if metodo_pago.startswith('---'): metodo_pago = "EFECTIVO"

    match_auth = re.search(r'Autorización:\s*(.+)', contenido_completo)
    autorizacion = f"'{match_auth.group(1).strip()}'" if match_auth else "NULL"

    id_ticket_actual = registro.seq_ticket
    registro.seq_ticket += 1

    return {
        'id_ticket': id_ticket_actual,
        'sql_ticket': (
            f"INSERT INTO ticket (id, numero_ticket, fecha_hora, total, id_sucursal, id_empleado) VALUES "
            f"({id_ticket_actual}, '{match_ticket.group(1)}', '{fecha_sql}', {total_con_iva:.2f}, {id_sucursal}, {id_empleado});"
        ),
        'items': items_procesados,
        'pago_data': (metodo_pago, total_con_iva, autorizacion)
    }

def generar_sql_final(registro, datos_procesados):
    sql = []

    for nom, info in registro.catalogos['sucursal'].items():
        sql.append(f"INSERT INTO sucursal (id, nombre, direccion, cif) VALUES ({info['id']}, '{nom}', '{info['datos']['direccion']}', '{info['datos']['cif']}');")

    for cod, info in registro.catalogos['empleado'].items():
        sql.append(f"INSERT INTO empleado (id, codigo_empleado, nombre) VALUES ({info['id']}, '{cod}', '{info['datos']['nombre']}');")

    for nom, info in registro.catalogos['producto'].items():
        sql.append(f"INSERT INTO producto (id, nombre) VALUES ({info['id']}, '{nom}');")

    for datos in datos_procesados:
        sql.append(datos['sql_ticket'])
        for (id_prod, cant, sub) in datos['items']:
            id_linea = registro.seq_linea
            registro.seq_linea += 1
            unit = sub / cant if cant else 0
            sql.append(f"INSERT INTO ticket_linea (id, id_ticket, id_producto, cantidad, precio_unitario, subtotal) VALUES ({id_linea}, {datos['id_ticket']}, {id_prod}, {cant}, {unit:.2f}, {sub:.2f});")
        
        id_pago = registro.seq_pago
        registro.seq_pago += 1
        met, mon, auth = datos['pago_data']
        sql.append(f"INSERT INTO pago (id, id_ticket, metodo_pago, monto, autorizacion) VALUES ({id_pago}, {datos['id_ticket']}, '{met}', {mon:.2f}, {auth});\n")

    return "\n".join(sql)

def main():
    carpeta_base = Path(__file__).parent
    carpeta_facturas = carpeta_base / "facturas"
    archivo_salida = carpeta_base / "InsertUnderlineTicket.sql"
    
    archivos = sorted(list(carpeta_facturas.glob("*.txt")))
    
    if not archivos:
        print("No hay archivos .txt en la carpeta 'facturas'")
        return

    print(f"Encontrados {len(archivos)} archivos. Procesando...")
    
    registro = IdRegistry()
    resultados = []
    
    for archivo in archivos:
        res = parsear_factura(archivo, registro)
        if res:
            resultados.append(res)
            
    if resultados:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(generar_sql_final(registro, resultados))
        print(f"Tickets procesados.")
        print(f"SQL generado en: {archivo_salida}")

        sql_runner_path = carpeta_base / "run_sql_xampp.py"
        
        if sql_runner_path.exists():
            print("\nEjecutando script de conexión a MySQL...")
            try:
                comando = [
                    "python", 
                    str(sql_runner_path), 
                    "--host", "localhost", 
                    "--user", "root", 
                    "--password", "root", 
                    "--database", "facturas",
                    "--sql-file", str(archivo_salida)
                ]
                
                subprocess.run(
                    comando, 
                    check=True 
                )
                
            except subprocess.CalledProcessError as e:
                print(f"\nError al ejecutar run_sql_xampp.py: El comando falló con código {e.returncode}.")
            except FileNotFoundError:
                print(f"\nError: No se encontró el ejecutable 'python' o el script '{sql_runner_path.name}'.")
            except Exception as e:
                print(f"\nError inesperado al ejecutar el script: {e}")
        else:
            print(f"\nAdvertencia: El archivo '{sql_runner_path.name}' no fue encontrado. Saltando la ejecución.")

if __name__ == "__main__":
    main()