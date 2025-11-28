import os
import argparse
import mysql.connector
from mysql.connector import errorcode


DEFAULT_SQL_FILE = os.path.join(os.path.dirname(__file__), 'InsertUnderlineTicket.sql')


CREATE_TABLES_SQL = r"""
SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS ticket_linea;
DROP TABLE IF EXISTS pago;
DROP TABLE IF EXISTS ticket;
DROP TABLE IF EXISTS producto;
DROP TABLE IF EXISTS empleado;
DROP TABLE IF EXISTS sucursal;

CREATE TABLE IF NOT EXISTS sucursal (
    id INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    direccion TEXT,
    cif VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS empleado (
    id INT PRIMARY KEY,
    codigo_empleado VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS producto (
    id INT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ticket (
    id INT PRIMARY KEY,
    numero_ticket VARCHAR(100) NOT NULL UNIQUE,
    fecha_hora DATETIME NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    id_sucursal INT NOT NULL,
    id_empleado INT,
    FOREIGN KEY (id_sucursal) REFERENCES sucursal(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (id_empleado) REFERENCES empleado(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_linea (
    id INT PRIMARY KEY,
    id_ticket INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (id_ticket) REFERENCES ticket(id) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES producto(id) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pago (
    id INT PRIMARY KEY,
    id_ticket INT NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    autorizacion VARCHAR(200),
    FOREIGN KEY (id_ticket) REFERENCES ticket(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS=1;
"""


CLEAN_TABLES_SQL = r"""
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE ticket_linea;
TRUNCATE TABLE pago;
TRUNCATE TABLE ticket;
TRUNCATE TABLE producto;
TRUNCATE TABLE empleado;
TRUNCATE TABLE sucursal;
ALTER TABLE sucursal AUTO_INCREMENT = 1;
ALTER TABLE empleado AUTO_INCREMENT = 1;
ALTER TABLE producto AUTO_INCREMENT = 1;
ALTER TABLE ticket AUTO_INCREMENT = 1;
ALTER TABLE ticket_linea AUTO_INCREMENT = 1;
ALTER TABLE pago AUTO_INCREMENT = 1;
SET FOREIGN_KEY_CHECKS=1;
"""


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1', help='MySQL host (XAMPP localhost)')
    p.add_argument('--port', type=int, default=3306, help='MySQL port')
    p.add_argument('--user', default='root', help='MySQL user')
    p.add_argument('--password', default='root', help='MySQL password')
    p.add_argument('--database', default='facturas', help='Nombre de la base de datos a crear/usar')
    p.add_argument('--sql-file', default=DEFAULT_SQL_FILE, help='Archivo SQL con INSERTs')
    return p.parse_args()


def connect_mysql(host, port, user, password, database=None):
    cfg = {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'autocommit': False,
    }
    if database:
        cfg['database'] = database
    return mysql.connector.connect(**cfg)


def create_database_if_not_exists(conn, dbname):
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        conn.commit()
        print(f"Base de datos '{dbname}' creada o ya existente.")
    finally:
        cursor.close()


def execute_multi_sql(conn, sql_text, filename=None):
    cursor = conn.cursor()
    try:
        try:
            for result in cursor.execute(sql_text, multi=True):
                if result.with_rows:
                    _ = result.fetchall()
            conn.commit()
            return
        except TypeError:
            cleaned = sql_text.replace('```sql', '').replace('```', '')
            statements = [s.strip() for s in cleaned.split(';')]
            for stmt in statements:
                if not stmt:
                    continue
                if stmt.lstrip().startswith('--'):
                    continue
                cursor.execute(stmt)
            conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error ejecutando SQL{(' en '+filename) if filename else ''}: {err}")
        raise
    finally:
        cursor.close()


def main():
    args = parse_args()

    try:
        conn = connect_mysql(args.host, args.port, args.user, args.password)
    except mysql.connector.Error as err:
        print(f"Error conectando a MySQL: {err}")
        return

    try:
        create_database_if_not_exists(conn, args.database)
    finally:
        conn.close()

    try:
        conn = connect_mysql(args.host, args.port, args.user, args.password, database=args.database)
    except mysql.connector.Error as err:
        print(f"Error conectando a la base de datos {args.database}: {err}")
        return

    try:
        execute_multi_sql(conn, CREATE_TABLES_SQL)
        print('Tablas creadas.')

        try:
            execute_multi_sql(conn, CLEAN_TABLES_SQL)
        except Exception:
            print('No se pudo truncar/reiniciar tablas; continuando con INSERTs.')

        sql_file = args.sql_file
        if not os.path.isabs(sql_file):
            sql_file = os.path.join(os.path.dirname(__file__), sql_file)

        if not os.path.exists(sql_file):
            print(f"Archivo SQL no encontrado: {sql_file}")
            return

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_text = f.read()

        wrapped_sql = 'SET FOREIGN_KEY_CHECKS=0;\n' + sql_text + '\nSET FOREIGN_KEY_CHECKS=1;'
        execute_multi_sql(conn, wrapped_sql, filename=sql_file)
        print('INSERTs ejecutados correctamente.')

    except Exception as e:
        print('Ocurrió un error:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    main()