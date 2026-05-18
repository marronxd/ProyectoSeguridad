"""
alojar.py

Descripción:
- Interfaz gráfica para crear/alojar un servidor

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

"""Importaciones"""
import servidorTCP
import utilerias as util
import tkinter as tk
from tkinter import messagebox as mb
import threading


protocolo_servidor = None

""" Verificación del protocolo: regresa la función iniciar según TCP/UDP """
def verificacionProtocolo(protocolo):
    global protocolo_servidor
    if protocolo == "TCP":
        protocolo_servidor = "TCP"
        return servidorTCP.iniciar

    

"""Oculta el menú y muestra esta pantalla"""
def mostrarFrame(ventana, frameMenu, protocolo="TCP"):
    frameMenu.pack_forget()
    frameAlojar = crearFrame(ventana, frameMenu, protocolo)
    frameAlojar.pack(fill="both", expand=True)


"""Regresa al menú principal"""
def regresar(frameAlojar, frameMenu):
    frameAlojar.pack_forget()
    frameMenu.pack(fill="both", expand=True)

"""Crea el frame"""
def crearFrame(ventana, frameMenu, protocolo="TCP"):
    framePrincipal = tk.Frame(ventana, bg=util.colorFondo)
    
    # Mostrar protocolo seleccionado
    util.label(framePrincipal, f"Crear servidor - Protocolo: {protocolo}", 18)
    
    campoServidor = util.frameInfo(framePrincipal, "Nombre del servidor", 20)
    campoAnfitrion = util.frameInfo(framePrincipal, "Anfitrión", 15)
    campoPuerto = util.frameInfo(framePrincipal, "Puerto del servidor", 5)
    
    def clickAlojar():
        servidor = campoServidor.get()
        puerto = campoPuerto.get()
        anfitrion = campoAnfitrion.get()
        
        if not servidor or not puerto:
            mb.showwarning("Campos vacíos", "Llene los campos solicitados")
            return
        
        if util.validarPuerto(puerto):
            try:
                funcion_iniciar = verificacionProtocolo(protocolo)
                
                hilo_servidor = threading.Thread(
                    target=lambda: funcion_iniciar(int(puerto)),
                    daemon=True
                )
                hilo_servidor.start()

                mb.showinfo(
                    "Servidor iniciado",
                    f"Servidor {protocolo} iniciado en puerto {puerto} gracias al anfitrión {anfitrion}"
                )

            except OSError as e:
                if e.errno in (48, 98):  # Puerto ocupado
                    mb.showerror("Error", f"El puerto {puerto} ya está en uso.")
                else:
                    mb.showerror("Error", f"No se pudo iniciar el servidor:\n{e}")

            except Exception as e:
                mb.showerror("Error inesperado", str(e))
            
            return

        mb.showerror("Error", "Puerto inválido")
    
    util.boton(framePrincipal, f"Alojar servidor {protocolo}", clickAlojar)
    util.boton(framePrincipal, "Regresar", lambda: regresar(framePrincipal, frameMenu))

    return framePrincipal
