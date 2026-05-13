"""
menu.py

Descripción:
- Módulo principal que permite elegir el protocolo de red (TCP o UDP) antes de iniciar la acción de conectar o alojar un servidor.

Funcionamiento:
- Despliega la interfaz principal para elegir el servicio (Unirse a un servidor o Crear un servidor) y el protocolo de comunicación.
- Captura la selección del usuario y pasa el protocolo elegido ('TCP' o 'UDP') a los módulos 'conectar.py' y 'alojar.py'.

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

"""Importaciones"""
import conectar # Módulo para el cliente: maneja la conexión a un servidor
import utilerias as util # Módulo de utilidades: funciones varias (validaciones, colores, obtención de IP)
import alojar # Módulo para el servidor: permite crear y alojar un servidor
import tkinter as tk # Biblioteca principal de interfaz gráfica
from tkinter import ttk # Necesario para usar el Combobox (lista desplegable de protocolos)
import login_gui
import login_validacion as logVal

"""Crea el frame principal del menú y lo configura"""
def crearFrame(ventana):
    frameMenu = tk.Frame(ventana, bg=util.colorFondo) # Crea el contenedor principal (la pantalla) y le asigna el color de fondo

    util.label(frameMenu, "POTROCHAT", 40) # Muestra el título principal del programa

    descripcion = f"Hola {logVal.USUARIO} bienvenido a GRINDER. Explora un mundo de posibilidades Homosexuales"
    util.label(frameMenu, descripcion, 15) # Muestra la descripción del programa

    # Frame contenedor para la etiqueta y el Combobox
    frameProtocolo = tk.Frame(frameMenu, bg=util.colorFondo)
    frameProtocolo.pack(pady=10)

    util.label(frameProtocolo, "Chat funcionando con TCP", 18)

    # Combobox de selección TCP. Ya no se meustra pero se quedó así por temas de funciones
    protocolo = ttk.Combobox(frameProtocolo, 
                             values=["TCP"], 
                             state="readonly", # No permite escribir texto, solo seleccionar
                             width=10)
    protocolo.current(0)  # Establece "TCP" como valor por defecto (índice 0)

    # Botón para unirse (Cliente). Usa lambda para ejecutar la función al hacer clic.
    # Llama a 'conectar.mostrarFrame', pasando el protocolo seleccionado dinámicamente con 'protocolo.get()'.
    util.boton(frameMenu, "Unirse a un servidor", 
              lambda: conectar.mostrarFrame(ventana, frameMenu, protocolo.get()))
 
    
    # Botón para crear (Servidor). Llama a 'alojar.mostrarFrame', pasando el protocolo seleccionado.
    util.boton(frameMenu, "Crear un servidor", 
               lambda: alojar.mostrarFrame(ventana, frameMenu, protocolo.get()))
    
    util.boton(frameMenu, "Salir", ventana.destroy) # Cierra la ventana y sale del programa

    util.labelIp(frameMenu) # Muestra la IP local del dispositivo para referencia

    return frameMenu # Regresa el contenedor principal del menú