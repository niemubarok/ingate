import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk  # PIL is used to handle images in tkinter

# Import missing modules and constants
from gpiozero import Button, OutputDevice
from threading import Thread
from pydub import AudioSegment
from pydub.playback import play

# Assuming you have these modules
# from db_functions import connect_to_database, check_id_pintu_masuk, save_to_database
from log_config import setup_logging
from global_variables import *
from escpos.printer import Usb, Network, Serial, CupsPrinter
from datetime import datetime
import os

import random
import string
import barcode
from barcode.writer import ImageWriter

from dotenv import load_dotenv
load_dotenv()

class ParkirApp:
    def __init__(self, root):
        self.status_loop1 = False
        self.status_loop2 = False

        self.root = root
        self.root.title("Parkir App")
        self.root.attributes('-fullscreen', True)

        # Create main frame with horizontal orientation
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create left frame for log, and make it smaller
        left_frame = tk.Frame(self.main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        self.log_label = tk.Label(left_frame, text="Log:")
        self.log_label.pack()

        self.log_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Create right frame for snapshot
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a frame for the canvas
        canvas_frame = tk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.snapshot_label = tk.Label(canvas_frame, text="Snapshot:")
        self.snapshot_label.pack()

        self.canvas = tk.Label(canvas_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.simulate_loop1_button = tk.Button(self.button_frame, text="Simulate Loop 1", command=self.simulate_loop1)
        self.simulate_loop1_button.pack(side=tk.LEFT)

        self.simulate_tombol_struk_button = tk.Button(self.button_frame, text="Simulate Tombol Struk", command=self.simulate_tombol_struk)
        self.simulate_tombol_struk_button.pack(side=tk.LEFT)

        self.simulate_loop2_button = tk.Button(self.button_frame, text="Simulate Loop 2", command=self.simulate_loop2)
        self.simulate_loop2_button.pack(side=tk.LEFT)

        self.setup_gpio() # Call setup_gpio method to set up GPIO


        connection_type = os.getenv("KONEKSI_PRINTER", "USB")  # Get the connection type from environment variable

        if connection_type == "USB":
            self.printer = Usb(0x0416, 0x5011)  # You need to replace these values with your printer's USB vendor and product IDs
        elif connection_type == "NETWORK":
            printer_ip = os.getenv("PRINTER_IP", "192.168.1.100")  # Replace with the actual IP address of your network printer
            self.printer = Network(printer_ip)
        elif connection_type == "SERIAL":
            serial_port = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")  # Replace with the actual serial port of your printer
            self.printer = Serial(serial_port)
        elif connection_type == "CUPS":
            self.printer = CupsPrinter()
        else:
            raise ValueError("Invalid connection type specified in KONEKSI_PRINTER environment variable")

    def simulate_loop1(self):
        self.loop1_callback()

    def simulate_tombol_struk(self):
        self.struk_callback()

    def simulate_loop2(self):
        self.loop2_callback()


    def setup_gpio(self):
        if self.is_raspberry_pi():
            from gpiozero import Button, LED

            loop1_sensor = Button(loop1)
            loop2_sensor = Button(loop2)
            tombol_struk_button = Button(tombol_struk_pin, pull_up=False)
            gate = LED(gate_pin)

            # Set callbacks for the buttons
            loop1_sensor.when_pressed = self.loop1_callback
            loop2_sensor.when_pressed = self.loop2_callback
            tombol_struk_button.when_pressed = self.struk_callback
        else:
            print("GPIO setup is not executed because the system is not running on a Raspberry Pi.")

    @staticmethod
    def is_raspberry_pi():
        try:
            with open('/proc/cpuinfo', 'r') as cpuinfo:
                for line in cpuinfo:
                    if line.startswith('Hardware'):
                        hardware_info = line.split(':')[1].strip()
                        return hardware_info in ['BCM2708', 'BCM2709', 'BCM2711', 'BCM2835', 'BCM2836', 'BCM2837']
        except IOError:
            pass
        return False


    


    def loop1_callback(self):
        if not self.status_loop1:
            self.status_loop1 = True
            self.update_log_text("Kendaraan terdeteksi!")
            # Memainkan audio.wav
            # self.play_audio_file('sounds/carengine.wav')
            print("Kendaraan Masuk")


    def play_audio_file(self,audio_file_path):
        def play_audio():
            sound = AudioSegment.from_wav(audio_file_path)
            play(sound)

        audio_thread = threading.Thread(target=play_audio, daemon=True)
        audio_thread.start()


    def tombol_struk_callback(self):
        if self.status_loop1:
            self.update_log_text("Tombol struk ditekan!")
            print("struk ditekan")

            # gate.on()
            print("gate terbuka")

            # Generate and print barcode
            barcode_data = self.generate_random_barcode()  # You need to implement this method

            # Get printer parameters from environment variables
            company_name = os.getenv("COMPANY_NAME", "Default Company")
            lokasi_parkir = os.getenv("lokasi_parkir", "Default Location")
            id_pintu_masuk = os.getenv("id_pintu_masuk", "Default Entrance ID")

            # Set up the printer
            self.printer.open()

            # Print the barcode and company information
            self.print_struk(self.printer, barcode_data, company_name, lokasi_parkir, id_pintu_masuk)

            # Close the printer connection
            self.printer.close()

            thread = Thread(target=self.take_snapshot)
            thread.daemon = True
            thread.start()
        else:
            self.update_log_text("Tombol struk tidak ditekan")
            print("struk tidak bisa ditekan")




    def generate_random_barcode(self):
        # Implement your barcode generation logic using python-barcode library
        # For example, generate a Code 128 barcode with a random data
        random_data = "1234567890"  # Replace with your data
        code128 = barcode.get('code128', random_data, writer=ImageWriter())
        barcode_path = code128.save('barcode')  # Save the barcode image
        return barcode_path


    def struk_callback(self):
        if self.status_loop1:
            self.update_log_text("Tombol struk ditekan!")
            print("struk ditekan")

            # gate.on()
            print("gate terbuka")

            # Generate and print barcode
            barcode_data = self.generate_random_barcode()  # You need to implement this method

            # Get printer parameters from environment variables
            nama_perusahaan = os.getenv("NAMA_PERUSAHAAN", "Default Company")
            lokasi_parkir = os.getenv("LOKASI_PARKIR", "Default Location")
            id_pintu_masuk = os.getenv("ID_PINTU_MASUK", "Default Entrance ID")

            # Set up the printer
            self.printer.open()

            # Print the barcode and company information
            self.print_struk(self.printer, barcode_data, nama_perusahaan, lokasi_parkir, id_pintu_masuk)

            # Close the printer connection
            self.printer.close()

            thread = Thread(target=self.take_snapshot)
            thread.daemon = True
            thread.start()
        else:
            self.update_log_text("Tombol struk tidak ditekan")
            print("struk tidak bisa ditekan")

    

    def print_struk(self, printer, barcode_data, nama_perusahaan, lokasi_parkir, id_pintu_Masuk):
    # Add the company and location information centered at the top
        printer.set(align='center')
        printer.text(f"{nama_perusahaan}\n{lokasi_parkir}\n\n")

        # Align the entrance ID and current time to the left
        printer.set(align='left')
        text = f"Entrance ID: {id_pintu_Masuk}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        printer.text(text)

        try:
            with open(barcode_data, 'rb') as barcode_file:
                # Skip null bytes when reading the barcode file
                barcode_content = barcode_file.read().replace(b'\x00', b'')
                printer.image(barcode_content)
        except Exception as e:
            print(f"Error reading or printing barcode: {e}")

        printer.cut()




    def update_log_text(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)  # Scroll to the bottom

    def loop2_callback(self):
        if self.status_loop1:
            self.update_log_text("Gate tertutup")
            self.status_loop1 = False
            self.status_loop2 = False

            # Clear snapshot
            if hasattr(self, 'snapshot_image'):
                self.canvas.config(image=None)
                self.canvas.image = None
                self.snapshot_image = None

    def take_snapshot(self):
        # Take a snapshot from the IP camera (for testing, use a placeholder image)
        snapshot_path = "snapshot.jpg"
        # os.system(f'curl -o {snapshot_path} {url_ip_camera}')

        # Update the snapshot in the GUI with the image resized to match the canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image = Image.open(snapshot_path)
        resized_image = image.resize((canvas_width, canvas_height))
        self.snapshot_image = ImageTk.PhotoImage(resized_image)

        self.canvas.config(image=self.snapshot_image, width=canvas_width, height=canvas_height)
        self.canvas.image = self.snapshot_image

    def on_stop(self):
        # self.gate.off()
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkirApp(root)
    app.play_audio_file('sounds/carengine.wav')  # Fixed self to app reference
    # root.protocol("WM_DELETE_WINDOW", app.on_stop)  # Handle window close event
    root.mainloop()
