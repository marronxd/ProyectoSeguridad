"""
main.py

Descripción:
- Módulo de apoyo que solo guarda y muestra las diferentes pantallas (frames) del programa

Funcionamiento:
- Recibe los diferentes frames del programa y los muestra según se navegue

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775

"""

"""Importaciones"""
import tkinter as tk #Interfaz gráfica
import menu #Pantalla de menú principal
import conectar #Pantalla para conectarse a un servidor
import alojar #Pantalla para crear un servidor
#import chat #Pantalla del chat
import utilerias as util #Funciones varias
import login_gui # Interfaz de login

ventana = tk.Tk() #Crea la ventana principal
ventana.title("Menú de servicios") #Título de la ventana
ventana.state("zoomed") #Pantalla completa
ventana.configure(bg=util.colorFondo) #Color de fondo
ventana.protocol("WM_DELETE_WINDOW", ventana.destroy) #Se puede con el botón x

# Se creará el frame después de un login éxitoso.
frameMenu = None
frameConectar = None
frameAlojar = None

"""Función para mostrar un frame y ocultar el otro"""
def mostrarFrame(frameMostrar):
    for frame in (frameMenu, frameConectar, frameAlojar):
        if frame:
            frame.pack_forget()
    frameMostrar.pack(fill="both", expand=True)

    """
    Se llama tras un login éxitoso.
    Crea los frames y se muestran
    """
def exito():
    global frameMenu, frameConectar, frameAlojar
    frameMenu = menu.crearFrame(ventana) #Crea la pantalla de menú
    frameConectar = conectar.crearFrame(ventana, frameMenu) #Crea la pantalla para unirse a un servidor
    frameAlojar = alojar.crearFrame(ventana, frameMenu) #Crea la pantalla para crear un servidor
    #frameChat = chat.crearChat(ventana, frameMenu) #Crea la pantalla del chat

    frameMenu.mostrar = mostrarFrame #Pasa la función a los frames
    frameConectar.mostrar = mostrarFrame
    frameAlojar.mostrar = mostrarFrame
    mostrarFrame(frameMenu) # Muestra el menú después del login éxitoso

"""
Función para cerrar el sistema
"""
def cerrar_programa():
    ventana.destroy()

# Inicia el login
login_gui.abrirLogin(ventana, exito) # Manda mensaje de éxito y lo reciben los métodos que ocupen
ventana.mainloop() #Bucle para que siga abierta la ventana
