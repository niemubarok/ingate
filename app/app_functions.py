import os
import time
from barcode import generate
from barcode.writer import ImageWriter
from tkinter import Tk, Text, Label, PhotoImage, Canvas, Scrollbar, END, Y
from db_functions import connect_to_database, check_id_pintu_masuk, save_to_database
from log_config import setup_logging
# import pygame
import RPi.GPIO as GPIO 
from pydub import AudioSegment
from pydub.playback import play
from global_variables import *
from PIL import Image, ImageTk
from threading import Thread, Lock
import time

gui_access_lock = Lock()

logger = setup_logging()
# Ganti URL_IP_CAMERA dengan URL yang sesuai dengan IP camera Anda
url_ip_camera = 'http://ip_camera/snapshot.cgi'

# Ambil nilai dari file .env
nama_perusahaan = os.getenv('NAMA_PERUSAHAAN', 'Default Perusahaan')
lokasi_parkir = os.getenv('LOKASI_PARKIR', 'Default Lokasi')
id_pintu_masuk = os.getenv('ID_PINTU_MASUK', '01')




# Inisialisasi Pygame
# pygame.mixer.init()

def generate_random_barcode():
    # Fungsi ini akan menghasilkan barcode dari nomor acak
    # Gantilah metode penghasilan nomor acak sesuai kebutuhan Anda
    random_number = "123456789"  # Ganti dengan nomor acak yang sesuai
    return generate('Code128', random_number, writer=ImageWriter())

def update_snapshot(canvas, snapshot_path):
    try:
        # Hapus gambar yang sudah ada di Canvas
        canvas.delete("all")

        # Ambil ukuran grid canvas
        canvas_width = canvas.winfo_reqwidth()
        canvas_height = canvas.winfo_reqheight()

        image = Image.open(snapshot_path)
        
        # Sesuaikan ukuran gambar dengan ukuran grid canvas
        resized_image = image.resize((canvas_width, canvas_height))

        # Tampilkan gambar di Canvas
        photo = ImageTk.PhotoImage(resized_image)
        canvas.config(width=canvas_width, height=canvas_height)
        canvas.create_image(0, 0, anchor='nw', image=photo)

    except Exception as e:
        print(f"Error updating snapshot: {e}")


def tombol_struk_callback(channel, log_text, canvas, snapshot_label, root):
    global status_loop1, status_loop2
    # id_pintu_masuk = check_id_pintu_masuk()
    # if id_pintu_masuk is None:
    #     logger.warning("Tidak dapat melanjutkan proses. Id pintu masuk belum dibuat.")
    #     return
    print(status_loop1)


    with gui_access_lock:
        if status_loop1:
            GPIO.output(gate_pin, GPIO.HIGH)
            logger.info("Tombol struk ditekan!")

            # Ganti 'YOUR_PRINTER_NAME' dengan nama printer yang benar
            # printer_name = 'YOUR_PRINTER_NAME'

            # # Generate barcode dan simpan sebagai gambar
            # barcode_image_path = 'barcode.png'
            # barcode = generate_random_barcode()
            # barcode.save(barcode_image_path)

            # # Ambil snapshot dari IP camera dengan curl
            snapshot_path = 'snapshot.jpg'
            # os.system(f'curl -o {snapshot_path} {url_ip_camera}')
            root.after(0, update_snapshot, canvas, snapshot_path)

            # # Simpan data ke dalam tabel transaksi_parkir
            # random_number = "123456789"  # Ganti dengan nomor acak yang sesuai
            # save_to_database(random_number, barcode_image_path, snapshot_path)

            # # Content to be printed
            # receipt_content = f"""
            #     {nama_perusahaan}
            #     {lokasi_parkir}
            #     Id Pintu Masuk : {id_pintu_masuk}
            #     Waktu          : {time.strftime("%d/%m/%Y %H:%M")}
                
            #     Barcode
            #     {barcode_image_path}

            #     Terima kasih
            #     """.center(20)

            # # Command for printing
            # print_command = 'echo "{}" | lp -d {}'.format(receipt_content, printer_name)
            # os.system(print_command)
            
            log_text.config(state='normal')
            log_text.insert(END, "Tombol struk ditekan!\n")
            log_text.config(state='disabled')

            status_loop2 = True

            # Update log dan snapshot di GUI
        else:
            logger.warning("Tombol struk tidak dapat ditekan!")


# def background_task():
#     while True:
#         # Ganti ini dengan logika aktual pengambilan gambar
#         time.sleep(1)
#         snapshot_path = "path_to_your_image.jpg"

#         # Gunakan Lock untuk memastikan akses yang aman ke variabel GUI dari thread
#         with gui_access_lock:
#             update_snapshot(canvas, snapshot_label, snapshot_path)


def loop1_callback(channel, log_text):
    global status_loop1
    if not status_loop1:
        status_loop1 = True
        print("Kendaraan terdeteksi!")
        log_text.config(state='normal')  # Aktifkan log_text untuk penambahan teks
        log_text.insert(END, "Kendaraan terdeteksi\n")
        log_text.config(state='disabled')

        # sound_file_path = 'sounds/carengine.wav'

        # # Ganti 'your_sound_file.wav' dengan nama file .wav yang ingin dijalankan
        # sound = AudioSegment.from_file(sound_file_path)
        # play(sound)

def loop2_callback(channel,log_text, canvas,snapshot_label):
    global status_loop1, status_loop2
    if status_loop1:
        GPIO.output(gate_pin, GPIO.LOW)
        logger.info("Gate tertutup")
        log_text.config(state='normal')
        log_text.insert(END, "Gate tertutup\n")
        log_text.config(state='disabled')
        status_loop1 = False
        status_loop2 = False

        # Clear snapshot
        canvas.config(width=1, height=1)  # Set ke ukuran minimum (1x1 pixel)
        snapshot_label.config(image=None)
    else:
        logger.warning("Status loop1 tidak sesuai.")




# update_thread = Thread(target=background_task)
# update_thread.daemon = True
# update_thread.start()