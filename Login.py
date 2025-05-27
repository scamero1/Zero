import streamlit as st
import json
import os

# --- CARGAR BASE DE DATOS DE USUARIOS ---
RUTA_USUARIOS = "usuarios.json"

def cargar_usuarios():
    if not os.path.exists(RUTA_USUARIOS):
        return {}
    with open(RUTA_USUARIOS, "r") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(RUTA_USUARIOS, "w") as f:
        json.dump(usuarios, f, indent=4)

# --- REGISTRO DE NUEVO USUARIO ---
def registrar_usuario(usuario, clave, rol):
    usuarios = cargar_usuarios()
    if usuario in usuarios:
        st.warning("⚠️ El usuario ya existe.")
        return
    usuarios[usuario] = {"clave": clave, "rol": rol}
    guardar_usuarios(usuarios)
    st.success(f"✅ Usuario '{usuario}' registrado con rol '{rol}'")

# --- VERIFICAR LOGIN ---
def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔐 Iniciar Sesión")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Iniciar"):
            usuarios = cargar_usuarios()
            if usuario in usuarios and usuarios[usuario]["clave"] == clave:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["rol"] = usuarios[usuario]["rol"]
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        st.stop()

# --- CERRAR SESIÓN ---
def logout():
    st.session_state.clear()
    st.success("🚪 Has cerrado sesión.")
    st.rerun()