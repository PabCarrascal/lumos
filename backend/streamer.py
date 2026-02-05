import subprocess
import os
import time
import threading
import re
import time

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


# Variable global para guardar la duración de las películas en orden
playlist_data = []

def generar_lista_y_titulos():
    global playlist_data
    playlist_data = []
    
    if not os.path.exists(HLS_PATH):
        os.makedirs(HLS_PATH, exist_ok=True)
    
    with open(PLAYLIST_FILE, "w") as f:
        for carpeta in ORDEN_CARPETAS:
            ruta = os.path.join(MEDIA_ROOT, carpeta)
            if os.path.exists(ruta):
                videos = [v for v in os.listdir(ruta) if v.lower().endswith(('.mp4', '.mkv'))]
                for v in sorted(videos):
                    video_path = os.path.join(ruta, v)
                    # Obtenemos duración aproximada usando ffprobe
                    duracion = obtener_duracion(video_path)
                    
                    titulo = re.sub(r'\s*\(\d{4}\)', '', carpeta).strip()
                    playlist_data.append({"titulo": titulo, "duracion": duracion})
                    
                    f.write(f"file '{video_path.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

def obtener_duracion(archivo):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{archivo}"'
        return float(os.popen(cmd).read().strip())
    except:
        return 9000  # Fallback 2.5h si falla

def monitorizar_titulos(proceso):
    # Ya no leemos logs, usamos el tiempo
    inicio_stream = time.time()
    while True:
        tiempo_actual = (time.time() - inicio_stream)
        
        # Calculamos el tiempo acumulado de la playlist
        duracion_total_playlist = sum(item['duracion'] for item in playlist_data)
        
        # Obtenemos el tiempo dentro del ciclo actual (por el loop -1 de ffmpeg)
        tiempo_en_ciclo = tiempo_actual % duracion_total_playlist
        
        acumulado = 0
        titulo_actual = "Harry Potter"
        
        for item in playlist_data:
            acumulado += item['duracion']
            if tiempo_en_ciclo < acumulado:
                titulo_actual = item['titulo']
                break
        
        with open(TITULO_FILE, "w") as f:
            f.write(titulo_actual)
        
        time.sleep(10) # Actualiza cada 10 segundos

def iniciar_ffmpeg():
    comando = [
        'ffmpeg', '-loglevel', 'error', '-nostats',
        '-re', '-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', PLAYLIST_FILE,
        '-map', '0:v:0', '-map', '0:a:0', 
        # --- CONFIGURACIÓN DE ALTO RENDIMIENTO PARA CPU ---
        '-c:v', 'libx264', 
        '-preset', 'ultrafast',   # Mínimo uso de CPU, máxima velocidad
        '-tune', 'zerolatency',   # Optimizado para streaming en vivo
        '-crf', '23',             # Calidad de imagen equilibrada
        '-maxrate', '3000k', 
        '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p',    # Compatibilidad universal (móviles/web)
        '-g', '50',               # Keyframes cada 2 segundos para HLS
        # --------------------------------------------------
        '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100',
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
