import os
from dotenv import load_dotenv

load_dotenv()  # Load nilai dari file .env

# Ganti parameter koneksi sesuai dengan konfigurasi PostgreSQL Anda
db_params = {
    'dbname': os.getenv('DB_NAME', 'nama_database_default'),
    'user': os.getenv('DB_USER', 'nama_pengguna_default'),
    'password': os.getenv('DB_PASSWORD', 'kata_sandi_default'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}
