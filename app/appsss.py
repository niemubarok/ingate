import RPi.GPIO as GPIO
import time
import os
import psycopg2
import logging
from barcode import generate
from barcode.writer import ImageWriter
from tkinter import Tk, Text, Label, PhotoImage, Canvas, Scrollbar, END, Y
from dotenv import load_dotenv
import pygame

load_dotenv()  # Load nilai dari file .env

loop1 = 18
loop2 = 27
tombol_struk_pin = 4
gate_pin = 24

status_loop1 = False
status_loop2 = False

# Ganti parameter koneksi sesuai dengan konfigurasi PostgreSQL Anda
db_params = {
    'dbname': os.getenv('DB_NAME', 'nama_database_default'),
    'user': os.getenv('DB_USER', 'nama_pengguna_default'),
    'password': os.getenv('DB_PASSWORD', 'kata_sandi_default'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Ganti URL_IP_CAMERA dengan URL yang sesuai dengan IP camera Anda
url_ip_camera = 'http://ip_camera/snapshot.cgi'

# Konfigurasi log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ambil nilai dari file .env
nama_perusahaan = os.getenv('NAMA_PERUSAHAAN', 'Default Perusahaan')
lokasi_parkir = os.getenv('LOKASI_PARKIR', 'Default Lokasi')
id_pintu_masuk = os.getenv('ID_PINTU_MASUK', '01')

# Inisialisasi Pygame
pygame.mixer.init()

def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('app_log.txt')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def generate_random_barcode():
    # Fungsi ini akan menghasilkan barcode dari nomor acak
    # Gantilah metode penghasilan nomor acak sesuai kebutuhan Anda
    random_number = "123456789"  # Ganti dengan nomor acak yang sesuai
    return generate('Code128', random_number, writer=ImageWriter())

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

def update_snapshot(canvas, snapshot_label, snapshot_path):
    snapshot_image = PhotoImage(file=snapshot_path)
    canvas.config(width=snapshot_image.width(), height=snapshot_image.height())
    canvas.create_image(0, 0, anchor='nw', image=snapshot_image)
    snapshot_label.config(image=snapshot_image)
    snapshot_label.image = snapshot_image

def loop1_callback(channel):
    global status_loop1
    if not status_loop2:
        status_loop1 = True
        print("Kendaraan terdeteksi!")

        # Ganti 'your_sound_file.wav' dengan nama file .wav yang ingin dijalankan
        sound_file_path = 'your_sound_file.wav'
        pygame.mixer.music.load(sound_file_path)
        pygame.mixer.music.play()

def loop2_callback(channel):
    global status_loop2, status_loop1
    if status_loop1:
        GPIO.output(gate_pin, GPIO.LOW)
        logger.info("Gate tertutup")
        status_loop1 = False
        status_loop2 = False
    else: 
        logger.warning("Status loop1 tidak sesuai.")

def tombol_struk_callback(channel, log_text, canvas, snapshot_label):
    global status_loop1, status_loop2
    id_pintu_masuk = check_id_pintu_masuk()
    if id_pintu_masuk is None:
        logger.warning("Tidak dapat melanjutkan proses. Id pintu masuk belum dibuat.")
        return

    if status_loop1:
        logger.info("Tombol struk ditekan!")

        # Ganti 'YOUR_PRINTER_NAME' dengan nama printer yang benar
        printer_name = 'YOUR_PRINTER_NAME'

        # Generate barcode dan simpan sebagai gambar
        barcode_image_path = 'barcode.png'
        barcode = generate_random_barcode()
        barcode.save(barcode_image_path)

        # Ambil snapshot dari IP camera dengan curl
        snapshot_path = 'snapshot.jpg'
        os.system(f'curl -o {snapshot_path} {url_ip_camera}')

        # Simpan data ke dalam tabel transaksi_parkir
        random_number = "123456789"  # Ganti dengan nomor acak yang sesuai
        save_to_database(random_number, barcode_image_path, snapshot_path)

        # Content to be printed
        receipt_content = f"""
            {nama_perusahaan}
            {lokasi_parkir}
            Id Pintu Masuk : {id_pintu_masuk}
            Waktu          : {time.strftime("%d/%m/%Y %H:%M")}
            
            Barcode
            {barcode_image_path}

            Terima kasih
            """.center(20)

        # Command for printing
        print_command = 'echo "{}" | lp -d {}'.format(receipt_content, printer_name)
        os.system(print_command)
        
        # Memainkan file .wav
        sound_file_path = 'your_sound_file.wav'  # Ganti dengan nama file .wav yang ingin dijalankan
        pygame.mixer.music.load(sound_file_path)
        pygame.mixer.music.play()

        GPIO.output(gate_pin, GPIO.HIGH)
        status_loop2 = True

        # Update log dan snapshot di GUI
        log_text.insert(END, "Tombol struk ditekan!\n")
        update_snapshot(canvas, snapshot_label, snapshot_path)
    else:
        logger.warning("Tombol struk tidak dapat ditekan!")

def main():
    setup_logging()

    root = Tk()
    root.title("Parkir Application")

    log_label = Label(root, text="Log:")
    log_label.grid(row=0, column=0, sticky='w')

    log_text = Text(root, height=20, width=40, wrap='word')
    log_text.grid(row=1, column=0, sticky='w', padx=10)
    log_text.config(state='disabled')

    scrollbar = Scrollbar(root, command=log_text.yview)
    scrollbar.grid(row=1, column=1, sticky='nsew')
    log_text['yscrollcommand'] = scrollbar.set

    snapshot_label = Label(root, text="Snapshot:")
    snapshot_label.grid(row=0, column=2, sticky='w')

    canvas = Canvas(root, width=320, height=240)
    canvas.grid(row=1, column=2, sticky='w', padx=10)

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(loop1, GPIO.IN)
        GPIO.setup(loop2, GPIO.IN)
        GPIO.setup(tombol_struk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(gate_pin, GPIO.OUT, initial=GPIO.LOW)
        
        GPIO.add_event_detect(loop1, GPIO.FALLING, callback=loop1_callback)
        GPIO.add_event_detect(loop2, GPIO.FALLING, callback=loop2_callback)
        GPIO.add_event_detect(tombol_struk_pin, GPIO.FALLING, callback=lambda x: tombol_struk_callback(x, log_text, canvas, snapshot_label))

        logger.info("Aplikasi berjalan. Tekan Ctrl+C untuk menghentikan.")

        root.mainloop()

    except KeyboardInterrupt:
        logger.info("Aplikasi dihentikan.")
        GPIO.cleanup()

    GPIO.cleanup()

if __name__ == "__main__":
    main()
