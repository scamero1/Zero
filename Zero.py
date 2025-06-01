import streamlit as st
from openai import OpenAI
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
import av
import numpy as np
import queue
import io
import pytesseract
from PIL import Image
import time
from Login import verificar_login, logout, registrar_usuario

# --- VERIFICAR LOGIN ANTES DE TODO ---
verificar_login()

# --- ESTILOS PERSONALIZADOS MÁS PROFESIONALES ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.sidebar-toggle-button {
    background-color: #008CBA;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: bold;
    text-align: center;
    cursor: pointer;
    margin-bottom: 15px;
}

.sidebar-toggle-button:hover {
    background-color: #005f6b;
}

/* Estilo para el chat */
.streamlit-expanderHeader {
    font-weight: 700;
}

.stChatMessage {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

[data-testid="stMarkdownContainer"] p {
    font-size: 1rem;
    line-height: 1.4;
}

.chat-assistant {
    background-color: #f0f4f8;
    border-radius: 15px;
    padding: 12px 20px;
    margin: 5px 0;
    color: #0a2540;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chat-user {
    background-color: #008CBA;
    border-radius: 15px;
    padding: 12px 20px;
    margin: 5px 0;
    color: white;
    font-weight: 600;
    text-align: right;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

</style>
""", unsafe_allow_html=True)

# --- MOSTRAR USUARIO Y ROL ARRIBA ---
st.markdown(f"<div class='sidebar-toggle-button'>👤 Usuario: {st.session_state['usuario']} | Rol: {st.session_state['rol']}</div>", unsafe_allow_html=True)

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "principal"

# --- MENÚ LATERAL SEGÚN ROL ---
menu_items = ["Principal"]
if st.session_state["rol"] == "admin":
    menu_items.extend(["Imagen", "Audio", "Registro de usuarios"])
menu_items.append("Cerrar sesión")

opcion = st.sidebar.selectbox("Menú", menu_items)

# --- FUNCIONES PARA LOGOUT Y RERUN ---
def do_logout():
    logout()
    st.experimental_rerun()

if opcion == "Cerrar sesión" or st.sidebar.button("🚪 Cerrar sesión"):
    do_logout()

# --- PAGINA REGISTRO (solo admins) ---
if opcion == "Registro de usuarios":
    if st.session_state["rol"] != "admin":
        st.warning("🔒 Solo administradores pueden acceder aquí.")
    else:
        st.title("📝 Registro de nuevo usuario")
        nuevo_usuario = st.text_input("Nuevo usuario")
        nueva_clave = st.text_input("Contraseña", type="password")
        nuevo_rol = st.selectbox("Rol", ["usuario", "admin"])
        if st.button("Registrar"):
            if nuevo_usuario.strip() == "" or nueva_clave.strip() == "":
                st.warning("Completa todos los campos")
            else:
                registrar_usuario(nuevo_usuario, nueva_clave, nuevo_rol)
                st.success(f"Usuario {nuevo_usuario} registrado.")
        if st.button("⬅️ Volver al chat"):
            st.session_state["pagina"] = "principal"
            st.rerun()

# --- HERRAMIENTA DE IMAGEN (solo admin) ---
elif opcion == "Imagen":
    st.title("🖼️ Herramienta de imagen")
    imagen = st.file_uploader("Sube una imagen (jpg, png, jpeg)", type=["jpg", "png", "jpeg"])
    if imagen is not None:
        try:
            st.image(imagen, use_container_width=True)
            texto = pytesseract.image_to_string(Image.open(imagen), lang="spa")
            st.success(f"📝 Texto reconocido:\n{texto}")
            st.session_state["msg"].append({"role": "user", "content": texto})
        except Exception as e:
            st.error(f"⚠️ Error al procesar imagen: {e}")

# --- HERRAMIENTA DE AUDIO (solo admin) ---
elif opcion == "Audio":
    st.title("🎙️ Herramienta de audio")
    audio_queue = queue.Queue()

    class AudioProcessor:
        def __init__(self):
            self.recognizer = sr.Recognizer()
        def recv(self, frame: av.AudioFrame):
            audio = frame.to_ndarray()
            audio = np.mean(audio, axis=0).astype(np.int16)
            audio_queue.put(audio)
            return av.AudioFrame.from_ndarray(audio, layout="mono")

    webrtc_streamer(
        key="voz",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"audio": True, "video": False},
        audio_processor_factory=AudioProcessor,
    )

    if st.button("🔊 Transcribir voz ahora"):
        try:
            recognizer = sr.Recognizer()
            audio_np = np.concatenate(list(audio_queue.queue), axis=0)
            audio_bytes = audio_np.tobytes()
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                texto = recognizer.recognize_google(audio, language="es-ES")
                st.success(f"🗣️ Texto reconocido: {texto}")
                st.session_state["msg"].append({"role": "user", "content": texto})
        except Exception as e:
            st.error(f"❌ Error al transcribir: {e}")

# --- CHAT PRINCIPAL ---
if opcion == "Principal" or opcion == "Cerrar sesión":

    st.title("🤖 ZERO - Asistente Virtual")

    if st.session_state["rol"] == "admin":
        st.success(f"👑 Bienvenido administrador {st.session_state['usuario']}")
    elif st.session_state["rol"] == "usuario":
        st.info(f"🙋‍♂️ ¡Hola {st.session_state['usuario']}! Bienvenido usuario")
    else:
        st.warning("⚠️ Rol no reconocido.")

    base = (
        "Zero es una inteligencia artificial avanzada diseñada para asistir a las personas..."
    )
    client = OpenAI(api_key="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")

    if "msg" not in st.session_state:
        # Mensaje inicial con bienvenida cálida personalizada
        saludo = f"¡Hola {st.session_state['usuario']}! 👋 Soy Zero, tu asistente personal. ¿En qué puedo ayudarte hoy?"
        st.session_state["msg"] = [{"role": "assistant", "content": saludo}]
    if "historial" not in st.session_state:
        st.session_state["historial"] = []

    # Mostrar mensajes anteriores con estilos personalizados
    for mensaje in st.session_state["msg"]:
        if mensaje["role"] == "assistant":
            st.markdown(f"<div class='chat-assistant'>{mensaje['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-user'>{mensaje['content']}</div>", unsafe_allow_html=True)

    # Entrada de usuario y respuesta IA
    if user_input := st.chat_input("Escribe tu mensaje aquí..."):
        st.session_state["msg"].append({"role": "user", "content": user_input})
        st.session_state["historial"].append(user_input)
        st.markdown(f"<div class='chat-user'>{user_input}</div>", unsafe_allow_html=True)

        try:
            respuesta = client.responses.create(
                model="gpt-4o-mini",
                instructions=base,
                input=st.session_state["msg"],
                max_output_tokens=1000,
            )
            output = respuesta.output_text
        except Exception as e:
            output = "⚠️ Error al conectarse con la IA."
            st.error(str(e))

        st.session_state["msg"].append({"role": "assistant", "content": output})
        placeholder = st.empty()
        typed_text = ""
        for char in output:
            typed_text += char
            placeholder.markdown(f"<div class='chat-assistant'>{typed_text}</div>", unsafe_allow_html=True)
            time.sleep(0.02)
