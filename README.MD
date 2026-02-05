# 🪄 LUMOS: Harry Potter Non-Stop Streamer

**Lumos** es una plataforma web minimalista y elegante diseñada para la retransmisión continua (24/7) de la saga de Harry Potter almacenada en un servidor local. A diferencia de un reproductor convencional, Lumos emite un flujo constante (HLS), permitiendo que cualquier usuario que se conecte vea la misma escena al mismo tiempo.

> *"Lumos: Deja que la magia brille"*

---

## 🛠️ Especificaciones Técnicas

La aplicación utiliza una arquitectura de tres capas para garantizar fluidez y bajo consumo de recursos:

* **Procesamiento de Video:** FFmpeg se encarga de la concatenación y transcodificación en tiempo real.
* **Gestión de Memoria:** Los segmentos de video se escriben en `/dev/shm` (RAM) para evitar el desgaste del HDD/SSD y reducir la latencia.
* **Servidor Web:** Nginx sirve los fragmentos estáticos de video mediante el protocolo HLS.
* **Interfaz de Usuario:** Frontend basado en Video.js con tipografía mágica y diseño adaptable.



---

## 📂 Estructura del Proyecto

```text
/var/www/lumos/
├── backend/
│   ├── streamer.py        # Motor de streaming en Python
│   └── playlist.txt       # Lista de rutas físicas generada dinámicamente
└── frontend/
    ├── index.html         # Interfaz web (Lumos UI)
    └── lumos-icon.png     # Identidad visual
