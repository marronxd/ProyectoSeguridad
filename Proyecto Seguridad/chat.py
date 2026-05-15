"""
Chat.py
Interfaz gráfica del cliente con soporte para:
✔ TCP
✔ UDP
✔ Mensajes privados desde combobox
✔ Detección de usuarios conectados/desconectados

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import encriptar
import utilerias as util
from cryptography.hazmat.primitives import serialization
import base64
import traceback
import datetime

class ClienteChat:
    """
    Maneja la lógica de red del cliente.
    Se encarga de la conexión, envío y recepción de mensajes para TCP y UDP.

    El self ayuda a que cada cliente tenga su objeto propio
    """

    def __init__(self, protocolo, ip, puerto):
        self.protocolo = protocolo
        self.ip = ip
        self.puerto = puerto
        self.socket = None
        self.nombre = None
        self.ejecutando = False
        self.codigo = "utf-8"
        self.llave_privada = None          
        self.llave_publica = None         
        self.llave_publica_servidor = None 
        self.llaves_otros_clientes = {} 

    """
    Inicia la conexión del cliente con el servidor.
    Realiza el handshake inicial para registrar el nombre de usuario.
    Retorna True si la conexión es exitosa, False en caso contrario.
    """
    def iniciar(self, nombre):

        self.nombre = nombre
        try:
            if self.protocolo == "TCP":
                self._iniciar_tcp()
            
            self.ejecutando = True
            return True
        except Exception as e:
            print(f"Error al iniciar cliente: {e}")
            raise e  # Relanzar la excepción para que la capture el llamador

    def _iniciar_tcp(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip, self.puerto))
        self.socket.settimeout(None)

        try:
            
            # Recibe llave pública del servidor 

            largo_llave = int.from_bytes(self.socket.recv(4), 'big')
            llave_servidor_bytes = self.socket.recv(largo_llave)
            self.llave_publica_servidor = serialization.load_pem_public_key(llave_servidor_bytes)
            util.guardar_log("Recibida llave pública del servidor", "info")

            # Generar llaves del cliente
            self.llave_privada, self.llave_publica = encriptar.generar_llaves()
            
            # Handshake: recibir solicitud de nombre
            datos = self.socket.recv(4096).decode(self.codigo)
            util.guardar_log(f"Handshake - recibido del servidor: {datos}", "debug")
            
            if "Nombre:" in datos or "nombre" in datos.lower():
                # Enviar nombre
                self.socket.sendall(self.nombre.encode(self.codigo))
                util.guardar_log(f"Handshake - enviado nombre: {self.nombre}", "debug")
                
                # Enviar llave pública del cliente
                llave_publica_bytes = self.llave_publica.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                self.socket.send(len(llave_publica_bytes).to_bytes(4, 'big'))
                self.socket.send(llave_publica_bytes)
                util.guardar_log("Handshake - llave pública enviada al servidor", "debug")
                
                # Recibir respuesta del servidor
                respuesta_servidor = self.socket.recv(4096).decode(self.codigo)
                util.guardar_log(f"Handshake - respuesta del servidor: {respuesta_servidor}", "debug")
                
                if "nombre en uso" in respuesta_servidor.lower():
                    self.socket.close() # cierra la conexion de quien intente unirse
                    raise ConnectionRefusedError(respuesta_servidor)
                
                # recibe las llaves de los demás clientes
                self.llaves_otros_clientes = {}  # Diccionario para guardar llaves
                
                # Usar timeout para recibir llaves (el servidor puede enviar 0 o más)
                self.socket.settimeout(0.5)
                while True:
                    try:
                        # Recibir tamaño de la llave
                        largo_llave_cliente = int.from_bytes(self.socket.recv(4), 'big')
                        # Recibir la llave
                        llave_otro_cliente_bytes = self.socket.recv(largo_llave_cliente)
                        
                        # Recibir tamaño del nombre (4 bytes)
                        largo_nombre = int.from_bytes(self.socket.recv(4), 'big')
                        # Recibir el nombre
                        nombre_otro_cliente = self.socket.recv(largo_nombre).decode(self.codigo)
                        
                        # Guardar la llave
                        llave_otro = serialization.load_pem_public_key(llave_otro_cliente_bytes)
                        self.llaves_otros_clientes[nombre_otro_cliente] = llave_otro
                        print(f"DEBUG - Recibida llave pública de {nombre_otro_cliente}")
                        
                    except socket.timeout:
                        break  # No hay más llaves
                    except Exception as e:
                        util.guardar_log(f"Error al recibir llave de otro cliente: {e}", "error")
                        break

                self.socket.settimeout(None)
        except socket.timeout:
            util.guardar_log("Timeout durante handshake con el servidor", "error")
            raise Exception("Timeout: El servidor no respondió")
        except Exception as e: 
            raise # Re-lanzamos la excepción para que el código que llamó a iniciar() la maneje.


    """"Ignorar, solo no lo elimino pq no me quiero fregar algo"""
    def _iniciar_udp(self):
        """
        Configura el socket UDP y envía el nombre de usuario como primer mensaje.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.sendto(self.nombre.encode(self.codigo), (self.ip, self.puerto))

    """
        Envía un mensaje al servidor, encriptándolo si es TCP
    """
    def enviar(self, mensaje):
        try:
            if self.protocolo == "TCP":
                # Encriptar el mensaje con la llave pública del servidor
                if self.llave_publica_servidor:
                    mensaje_encriptado = encriptar.encriptar(mensaje, self.llave_publica_servidor)
                    self.socket.sendall(mensaje_encriptado)
                else:
                    # Si no hay llave del servidor, enviar sin encriptar (fallback)
                    self.socket.sendall(mensaje.encode(self.codigo)) # el sendall toma el paquete y lo envia varias veces hasta q se envia todo
            return True
        
        except Exception as e:
            print(f"Error al enviar: {e}")
            return False
    
    """
        Envía un mensaje privado formateado, encriptando solo el contenido
    """
    def enviar_privado_formateado(self, destino, contenido):

        try:
            contenido_encriptado = encriptar.encriptar(contenido, self.llave_publica_servidor) # encripta el contenido junto con la llave publica del server
            contenido_b64 = base64.b64encode(contenido_encriptado).decode(self.codigo) # pase 64 solo para transporte
            paquete = f"/p|{destino}|{contenido_b64}"
            self.socket.sendall(paquete.encode(self.codigo))
            return True
        
        except Exception as e:
            util.guardar_log(f"Error al enviar privado: {e}", "error")
            traceback.print_exc()
            return False


    """
        Recorre un hilo individualmente para recibir los mensajes que el servidor le envía
        para procesarlos y mostrarlos en la interfaz gráfica.
    """
    def bucle_recibir(self, callback):

        try:
            while self.ejecutando: # Mientras el cliente está activo
                try:
                    if self.protocolo == "TCP": # Ignorar solo es pq se manejaba tcp y udp
                        datos = self.socket.recv(4096) # Recibe los bytes del servidor
                        if not datos:
                            util.guardar_log("Conexión cerrada por el servidor", "warning")
                            break
                        
                        mensaje = None # Declararla por si las moscas
                        # Intentar desencriptar
                        try:
                            mensaje = encriptar.desencriptar(datos, self.llave_privada)
                        except Exception as e:

                            # Decodificarlo como texto plano. Flujo para mensajes de sistema

                            try:
                                mensaje = datos.decode(self.codigo)
                                util.guardar_log(f"Mensaje recibido del sistem: {mensaje}", "debug")
                            except UnicodeDecodeError as ude:
                                util.guardar_log(f"Error: {ude}", "error")
                                continue

                        if mensaje:
                            # Ahora llamamos al callback con protección adicional
                            try:
                                callback(mensaje)
                            except Exception as e:
                                traceback.print_exc()
                except Exception as e:
                    util.guardar_log(f"Error en bucle de recepción: {e}", "error")
                    break
        finally:
            self.ejecutando = False

    """
        Cierra el socket de red de forma segura.
    """
    def cerrar(self):

        self.ejecutando = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass


class VentanaChat:
    """
    Gestiona la interfaz gráfica (GUI) de la ventana de chat.
    Se encarga de mostrar mensajes y manejar la interacción del usuario.
    """
    def __init__(self, ventana_principal, ip, puerto, nombre, protocolo):
        self.ventana_principal = ventana_principal
        self.ip = ip
        self.puerto = puerto
        self.nombre = nombre
        self.protocolo = protocolo
        self.llave_privada = None
        self.llave_publica = None
        self.llave_publica_servidor = None  # <-- Para guardar llave del servidor
        self.crear_ventana()
        self.configurar_interfaz()

        if not self.iniciar_cliente():
            return

    def crear_ventana(self):
        """
        Crea y configura la ventana Toplevel para el chat.
        """
        self.ventana_chat = tk.Toplevel(self.ventana_principal)
        self.ventana_chat.title(f"Chat - {self.nombre} ({self.protocolo})")
        self.ventana_chat.minsize(500, 400)
        self.centrar_ventana(700, 500)
        self.ventana_chat.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def configurar_interfaz(self):
        """
        Construye y posiciona todos los widgets (botones, etiquetas, etc.) en la ventana de chat.
        """
        # --- Frame Superior (Techo) ---
        frame_techo = tk.Frame(self.ventana_chat, bg="#85dcff", height=40)
        frame_techo.pack(side='top', fill='x', padx=5, pady=5)
        tk.Label(
            frame_techo,
            text=f"Conectado como {self.nombre} ({self.protocolo})",
            bg="#85dcff",
            font=("Arial", 12)
        ).pack(pady=5)

       
        # Contiene los controles para enviar mensajes
        pie = tk.Frame(self.ventana_chat, height=50)
        pie.pack(padx=10, pady=10, side="bottom", fill="x")

        # Instrucción para mensajes privados
        comando_privado = "/p" if self.protocolo == "TCP" else "/privado"
        tk.Label(pie, text=f"Usa '{comando_privado} <nombre> <mensaje>' para privado").pack(side="top", anchor="w")

        self.campo_entrada = tk.Entry(pie)
        self.campo_entrada.bind("<Return>", lambda e: self.al_enviar())
        self.campo_entrada.pack(side="left", expand=True, fill="x", pady=(5,0))

        tk.Button(pie, text="Enviar", command=self.al_enviar).pack(side="right", padx=10)

        # ---------------- ÁREA DE MENSAJES ----------------
        frame_mensajes = tk.Frame(self.ventana_chat, bg="#f0f0f0", bd=3, relief=tk.SUNKEN)
        frame_mensajes.pack(fill='both', expand=True, padx=10, pady=5)

        self.texto_mensajes = tk.Text(
            frame_mensajes, wrap=tk.WORD, bg="white", fg="black",
            state=tk.DISABLED, padx=5, pady=5, relief=tk.FLAT
        )
        scrollbar = tk.Scrollbar(frame_mensajes, command=self.texto_mensajes.yview)
        self.texto_mensajes.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.texto_mensajes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def iniciar_cliente(self):
        """
        Crea una instancia del ClienteChat y arranca el hilo de recepción de mensajes.
        Muestra un error si la conexión inicial falla.
        Retorna True si el cliente se inicia correctamente, False en caso contrario.
        """
        self.cliente = ClienteChat(self.protocolo, self.ip, self.puerto)

        try:
            if not self.cliente.iniciar(self.nombre):
                messagebox.showerror("Error", "No se pudo conectar al servidor")
                self.ventana_chat.destroy()
                return False
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))
            self.ventana_chat.destroy()
            return False

        self.mostrar_mensaje_sistema(f"Conectado a {self.ip}:{self.puerto}")
        print(f"DEBUG - El callback es: {self.manejar_mensaje_entrante}")
        threading.Thread(
            target=self.cliente.bucle_recibir,
            args=(self.manejar_mensaje_entrante,),
            daemon=True
        ).start()
        return True

    def centrar_ventana(self, w, h):
        """
        Calcula la posición para centrar la ventana en la pantalla.
        """
        cx = (self.ventana_chat.winfo_screenwidth() // 2) - (w // 2)
        cy = (self.ventana_chat.winfo_screenheight() // 2) - (h // 2)
        self.ventana_chat.geometry(f"{w}x{h}+{cx}+{cy}")

    def al_enviar(self):
        texto = self.campo_entrada.get().strip()
        if not texto:
            return

        if texto.startswith("/p "):
            partes = texto.split(" ", 2)
            if len(partes) == 3:
                destino = partes[1]
                contenido = partes[2]
                # Usar el nuevo método que encripta solo el contenido
                self.cliente.enviar_privado_formateado(destino, contenido)
        else:
            # Mensaje público
            paquete = f"/PUBLICO|TODOS|({util.ahora()}) {self.nombre}: {texto}"
            self.cliente.enviar(paquete)
            self.mostrar_mensaje(self.nombre, texto, es_propio=True)

        self.campo_entrada.delete(0, tk.END)

    def manejar_mensaje_entrante(self, mensaje):
        """
        Recibe un mensaje del hilo de red y lo pone en la cola de eventos
        de Tkinter para ser procesado de forma segura en el hilo principal de la GUI.
        """
        print(f"DEBUG - self.ventana_chat: {self.ventana_chat}")
        print(f"DEBUG - ENTRANDO a manejar_mensaje_entrante, mensaje: {mensaje[:50] if mensaje else 'None'}")
        self.ventana_chat.after(0, self._procesar_mensaje_en_ui, mensaje)

    def _procesar_mensaje_en_ui(self, texto):
        """
        Se ejecuta en el hilo de la GUI.
        El texto YA VIENE DESENCRIPTADO de bucle_recibir()
        """
        
        #  Mensajes privados (formato del servidor) 
        if texto.startswith("(privado de") or texto.startswith("(privado para"):
            try:
                info, resto = texto.split(":", 1)
                resto = resto.strip()
                
                # El contenido está en base64, descodificar y desencriptar
                if resto:

                    try:
                        # Convertir de base64 a bytes
                        contenido_bytes = base64.b64decode(resto.encode(self.cliente.codigo))
                        # Desencriptar
                        mensaje_real = encriptar.desencriptar(contenido_bytes, self.cliente.llave_privada)

                    except Exception as e:
                        util.guardar_log(f"Error al desencriptar mensaje privado: {e}", "error")
                        mensaje_real = resto

                else:
                    mensaje_real = resto
                
                if info.startswith("(privado de"):
                    remitente = info.split(" ")[2].strip(")")
                    self.mostrar_mensaje(remitente, f"→ {mensaje_real}", es_privado=True)

                else:
                    destinatario = info.split(" ")[2].strip(")")
                    self.mostrar_mensaje(self.nombre, f"→ {destinatario}: {mensaje_real}", 
                                    es_propio=True, es_privado=True)
                return
            
            except Exception as e:
                util.guardar_log(f"Error en privado: {e}", "error")
                self.mostrar_mensaje_sistema(texto)
                return
        
        #  Mensajes con pipe (públicos del servidor) 
        if "|" in texto:
            try:
                partes = texto.split("|", 2)

                if len(partes) == 3:
                    tipo = partes[0]      # /PUBLICO o /p
                    destino = partes[1]   # TODOS o nombre
                    contenido = partes[2] # (fecha) nombre: mensaje
                    
                    if ": " in contenido:
                        prefijo, mensaje = contenido.rsplit(": ", 1)
                        
                        if "SERVIDOR" in prefijo:
                            self.mostrar_mensaje_sistema(mensaje)
                        else:
                            nombre = prefijo.split()[-1] if prefijo.split() else "Usuario"
                            self.mostrar_mensaje(nombre, mensaje, 
                                            es_propio=(nombre == self.nombre))
                        return
            except Exception as e:
                self.mostrar_mensaje_sistema(texto)
                return
        
        # Mensajes del sistema
        if "se unió al chat" in texto or "dejó el chat" in texto:
            self.mostrar_mensaje_sistema(texto)
            return
        
        # Cualquier otro mensaje 
        if ":" in texto:
            partes = texto.split(":", 1)
            remitente = partes[0].split()[-1] if partes[0].split() else "Usuario"
            self.mostrar_mensaje(remitente, partes[1].strip(), 
                            es_propio=(remitente == self.nombre))
        else:
            self.mostrar_mensaje_sistema(texto)

    def mostrar_mensaje_sistema(self, mensaje):
        """
        Wrapper para mostrar un mensaje con el estilo de 'Sistema'.
        """
        self.mostrar_mensaje("Sistema", mensaje)

    def mostrar_mensaje(self, remitente, mensaje,
                        es_propio=False, es_privado=False):

        """
        Inserta un mensaje formateado y coloreado en el área de texto del chat.
        Define y aplica etiquetas (tags) de Tkinter para dar estilo al texto
        (color para mensajes propios, privados, de sistema, etc.).
        """

        self.texto_mensajes.config(state=tk.NORMAL)

        # Define los estilos en español
        if "sistema" not in self.texto_mensajes.tag_names():
            self.texto_mensajes.tag_configure("sistema", foreground="blue")
            self.texto_mensajes.tag_configure("propio", foreground="green")
            self.texto_mensajes.tag_configure("otro", foreground="black")
            self.texto_mensajes.tag_configure("privado", foreground="purple")
            self.texto_mensajes.tag_configure("hora", foreground="gray")

        if remitente == "Sistema":
            tag = "sistema"
        elif es_privado:
            tag = "privado"
        elif es_propio:
            tag = "propio"
        else:
            tag = "otro"

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        self.texto_mensajes.insert(tk.END, f"[{timestamp}] ", ("hora",))
        self.texto_mensajes.insert(tk.END, f"{remitente}", (tag,))
        self.texto_mensajes.insert(tk.END, f": {mensaje}\n")

        self.texto_mensajes.config(state=tk.DISABLED)
        self.texto_mensajes.see(tk.END)

    
   
    def al_cerrar(self):
        """
        Se ejecuta cuando el usuario cierra la ventana de chat.
        Se asegura de cerrar la conexión de red antes de destruir la ventana.
        """
        try:
            self.cliente.cerrar()
        except:
            pass

        self.ventana_chat.destroy()


def iniciar_chat(ventana, ip, puerto, nombre, protocolo):
    """
    Función de entrada para crear y lanzar una nueva ventana de chat.
    """
    return VentanaChat(ventana, ip, puerto, nombre, protocolo)
