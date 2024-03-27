import psycopg2
from db_config import db_params
from log_config import setup_logging

logger = setup_logging()

def connect_to_database():
    try:
        connection = psycopg2.connect(**db_params)
        return connection
    except psycopg2.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        return None

def check_id_pintu_masuk():
    connection = connect_to_database()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_pintu_masuk FROM config_hardware")
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    logger.warning("Id pintu masuk belum dibuat di tabel config_hardware.")
                    return None
        except psycopg2.Error as e:
            logger.error(f"Error executing SQL query: {e}")
        finally:
            connection.close()
    return None

def save_to_database(random_number, barcode_path, snapshot_path):
    connection = connect_to_database()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Ganti 'transaksi_parkir' dengan nama tabel yang benar
                query = f"INSERT INTO transaksi_parkir (random_number, pic_barcode_masuk, pic_body_masuk) VALUES ('{random_number}', '{barcode_path}', '{snapshot_path}')"
                cursor.execute(query)
                connection.commit()
                logger.info("Data berhasil disimpan ke database.")
        except psycopg2.Error as e:
            logger.error(f"Error executing SQL query: {e}")
        finally:
            connection.close()

