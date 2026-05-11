import tkinter as tk
from tkinter import messagebox
import menu #Pantalla de menú principal
import utilerias as util
import hashlib as hash

"""
Almacen de usuarios

"""

usuarios  = {
    "aaron": "123",
    "cachorrita123": "pato"
    }




"""
Crear el frame tipo dialogo que muestyre el inicio de sesion

"""

def abrirLogin(ventana, exito):
   # Creacion de la ventana de diálogo (Toplevel)
    ventana_login = tk.Toplevel(ventana)
    
    # Configurar el título
    ventana_login.title("Inicio de Sesión")
    
    # Definir el tamaño (Ancho x Alto) y centrar
    screen_width = ventana_login.winfo_screenwidth() #estos extraen la medida de la ventana
    screen_height = ventana_login.winfo_screenheight()
    x = (screen_width - 300) // 2
    y = (screen_height - 250) // 2
    ventana_login.geometry(f"300x250+{x}+{y}")
    
    # Hacerla "Modal" o sea, que no se interactue con otra cosa
    ventana_login.grab_set()

    # --- Elementos de la interfaz ---
    
    # para el campo nombre/user
    tk.Label(ventana_login, text="Usuario:").pack(pady=(20, 0))
    entrada_user = tk.Entry(ventana_login)
    entrada_user.pack(pady=5)
    
    # para el campo de contrasenia
    tk.Label(ventana_login, text="Contraseña:").pack(pady=(10, 0))
    # show="*" para no mostrar la contrasenia
    entrada_contra = tk.Entry(ventana_login, show="*") 
    entrada_contra.pack(pady=5)
    


    def validar():

        # Extracción de la información de sus respectivos campos
        usuario = entrada_user.get()
        contrasenia = entrada_contra.get()

        # Verificacion de las entradas
        if usuario in usuarios: 
            if usuarios[usuario] == contrasenia:
                # Se destruye el login  y se avisa que fue un exito el inicio de sesión.
                ventana_login.destroy()
                exito()
        else: 
            messagebox.showerror("Error.", "Fallo de autenticación.")
    btn_entrar = tk.Button(ventana_login, text="Entrar", command=lambda: validar())
    btn_entrar.pack(pady=20)
