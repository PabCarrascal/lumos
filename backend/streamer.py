import subprocess
import os
import time
import threading
import re

HLS_PATH = "/dev/shm/hls_lumos"
TITULO_FILE = os.path.join(HLS_PATH, "titulo.txt")
MEDIA_ROOT = "/media/HDD3TB/PELICULAS/movies/harry potter/"
PLAYLIST_FILE = "/var/www/lumos/backend/playlist.txt"

ORDEN_CARPETAS = [
    "Harry Potter y la Piedra Filosofal (2001)",
    "Harry Potter y la Camara Secreta (2002)",
    "Harry Potter y el Prisionero de Azkaban (2004)",
    "Harry Potter y el Caliz de Fuego (2005)",
    "Harry Potter y la orden del Fenix (2007)",
    "Harry Potter y el misterio del Principe (2009)",
    "Harry Potter y las Reliquias de la Muerte 1 (2010)",
    "Harry Potter y las Reliquias de la Muerte 2 (2011)"
]

def generar_lista_y_titulos():
    if not os.path.exists(HLS_PATH):
        os.makedirs(HLS_PATH, exist_ok=True)
    
    with open(PLAYLIST_FILE, "w") as f:
        for carpeta in ORDEN_CARPETAS:
            ruta = os.path.join(MEDIA_ROOT, carpeta)
            if os.path.exists(ruta):
                videos = [v for v in os.listdir(ruta) if v.lower().endswith(('.mp4', '.mkv'))]
                for v in sorted(videos):
                    video_path = os.path.join(ruta, v)
                    f.write(f"file '{video_path.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

def monitorizar_titulos(proceso):
    while True:
        linea = proceso.stderr.readline()
        if not linea:
            break
        linea_str = linea.decode('utf-8', errors='ignore')
        if "Opening" in linea_str and MEDIA_ROOT in linea_str:
            try:
                match = re.search(r"'(.*?)'", linea_str)
                if match:
                    ruta_completa = match.group(1)
                    nombre_archivo = os.path.basename(ruta_completa)
                    titulo = os.path.splitext(nombre_archivo)[0]
                    titulo = re.sub(r'\s*[\(\{\[][^\]\}\)]*[\]\}\)]', '', titulo)
                    titulo = titulo.replace('.', ' ').replace('-', ' ').replace('_', ' ')
                    titulo = ' '.join(titulo.split()).strip()
                    with open(TITULO_FILE, "w") as f:
                        f.write(titulo)
                        f.flush()
            except Exception:
                pass

def iniciar_ffmpeg():
    comando = [
        'ffmpeg', '-loglevel', 'debug', '-nostats',
        '-re', '-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', PLAYLIST_FILE,
        '-map', '0:v:0', '-map', '0:a:m:language:spa?',
        '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k', '-maxrate', '3000k', '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p', '-g', '50', 
        '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100',
        '-af', 'aresample=async=1', '-vsync', 'cfr',
        '-f', 'hls', '-hls_time', '4', '-hls_list_size', '5', '-hls_flags', 'delete_segments',
        os.path.join(HLS_PATH, 'live.m3u8')
    ]
    return subprocess.Popen(comando, stderr=subprocess.PIPE, bufsize=0)

if __name__ == "__main__":
    generar_lista_y_titulos()
    if not os.path.exists(TITULO_FILE):
        with open(TITULO_FILE, "w") as f: f.write("Lanzando hechizo Lumos...")
    
    while True:
        proceso = iniciar_ffmpeg()
        hilo_titulos = threading.Thread(target=monitorizar_titulos, args=(proceso,), daemon=True)
        hilo_titulos.start()
        proceso.wait()
        time.sleep(5)
