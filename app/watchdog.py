from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type in ('modified', 'created'):
            print(f'Restarting due to {event.event_type} of file {event.src_path}')
            subprocess.run(['python', 'app.py'])

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
