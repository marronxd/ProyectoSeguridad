import tkinter as tk
from tkinter import messagebox
import menu #Pantalla de menú principal
import utilerias as util
import login_validacion as loginVal

"""
Almacen de usuarios


Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

"""
Crear el frame tipo dialogo que muestra el inicio de sesion

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
    
    # para el campo de contraseña
    tk.Label(ventana_login, text="Contraseña:").pack(pady=(10, 0))
    entrada_contra = tk.Entry(ventana_login, show="*") # show="*" para no mostrar la contrasenia
    entrada_contra.pack(pady=5)
    
    ventana_login.protocol("WM_DELETE_WINDOW", ventana.destroy) # si se le da a la x, cierra todo el programa


    """
    Función que llama a un auxiliar para validar la identidad.

    """
    def validar():

        # Extracción de la información de sus respectivos campos
        usuario = entrada_user.get().strip()
        contrasenia = entrada_contra.get().strip()

        # Verifica las entradas
        if loginVal.validar_identidad(usuario, contrasenia):
            util.guardar_log("Exito de inicio de sesión.", "info")
            # Se destruye el login  y se avisa que fue un exito el inicio de sesión.
            ventana_login.destroy()
            exito()
        else: 
            messagebox.showerror("Error.", "Fallo de autenticación.")
    btn_entrar = tk.Button(ventana_login, text="Entrar", command=lambda: validar())
    btn_entrar.pack(pady=20)
