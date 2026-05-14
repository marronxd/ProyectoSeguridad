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

class ClienteChat:
    """
    Maneja la lógica de red del cliente.
    Se encarga de la conexión, envío y recepción de mensajes para TCP y UDP.
    """

    def __init__(self, protocolo, ip, puerto):
        self.protocolo = protocolo
        self.ip = ip
        self.puerto = puerto
        self.socket = None
        self.nombre = None
        self.ejecutando = False
        self.codigo = "utf-8"

    def iniciar(self, nombre):
        """
        Inicia la conexión del cliente con el servidor.
        Realiza el handshake inicial para registrar el nombre de usuario.
        Retorna True si la conexión es exitosa, False en caso contrario.
        """
        self.nombre = nombre
        try:
            if self.protocolo == "TCP":
                self._iniciar_tcp()
            # elif self.protocolo == "UDP":  # Si tienes UDP después
            #     self._iniciar_udp()
            
            self.ejecutando = True
            return True
        except Exception as e:
            print(f"Error al iniciar cliente: {e}")
            raise e  # Relanzar la excepción para que la capture el llamador

    def _iniciar_tcp(self):
        """
        Establece una conexión TCP y realiza el handshake para validar el nombre.
        Lanza una excepción si el nombre ya está en uso o si la conexión falla.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip, self.puerto))
        self.socket.settimeout(None)

        try:
            # PRIMERO: Esperar a que el servidor pida el nombre
            datos = self.socket.recv(1024).decode(self.codigo)
            print(f"DEBUG - Servidor dice: {datos}")  # Para debug
            
            # SEGUNDO: Enviar el nombre cuando el servidor lo pida
            if "Nombre:" in datos or "nombre" in datos.lower():
                self.socket.sendall(self.nombre.encode(self.codigo))
                print(f"DEBUG - Nombre enviado: {self.nombre}")
                
                # TERCERO: Esperar respuesta del servidor
                respuesta_servidor = self.socket.recv(1024).decode(self.codigo)
                print(f"DEBUG - Respuesta servidor: {respuesta_servidor}")
                
                if "nombre en uso" in respuesta_servidor.lower():
                    self.socket.close()
                    raise ConnectionRefusedError(respuesta_servidor)
        except socket.timeout:
            raise Exception("Timeout: El servidor no respondió")
        except Exception as e:
            raise  # Re-lanzamos la excepción para que el código que llamó a iniciar() la maneje.

    def _iniciar_udp(self):
        """
        Configura el socket UDP y envía el nombre de usuario como primer mensaje.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.sendto(self.nombre.encode(self.codigo), (self.ip, self.puerto))

    def enviar(self, mensaje):
        """
        Envía un mensaje al servidor usando el protocolo correspondiente.
        Retorna True si el envío fue exitoso, False en caso de error.
        """
        try:
            if self.protocolo == "TCP":
                self.socket.sendall(mensaje.encode(self.codigo))
            return True
        except:
            return False

    def bucle_recibir(self, callback):
        """
        Bucle principal que escucha constantemente los mensajes del servidor.
        Cuando recibe un mensaje, lo decodifica y lo pasa a la función
        'callback' para que sea procesado por la interfaz de usuario.
        """
        try:
            while self.ejecutando:
                try:
                    if self.protocolo == "TCP":
                        datos = self.socket.recv(1024)
                        if not datos:
                            break
                        mensaje = datos.decode(self.codigo)
                        print(f"DEBUG - Mensaje recibido (crudo): {repr(mensaje)}")  # Debug
                        
                        # El servidor podría enviar múltiples mensajes juntos
                        # Separar por saltos de línea si existen
                        if '\n' in mensaje:
                            for msg in mensaje.split('\n'):
                                if msg.strip():
                                    callback(msg.strip())
                        else:
                            callback(mensaje)
                            
                except Exception as e:
                    print(f"Error en bucle_recibir: {e}")
                    break
        finally:
            self.ejecutando = False

    def cerrar(self):
        """
        Cierra el socket de red de forma segura.
        """
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
        """
        Se ejecuta al presionar 'Enviar' o la tecla Enter.
        Formatea el mensaje (público o privado) y lo envía a través del cliente de red.
        """
        texto = self.campo_entrada.get().strip()
        if not texto:
            return

        if texto.startswith("/p "):
            # Mensaje privado
            partes = texto.split(" ", 2)
            if len(partes) == 3:
                destino = partes[1]
                contenido = partes[2]
                mensaje_encriptado = encriptar.encriptar(contenido)
                # Formato que espera el servidor TCP
                paquete = f"/p|{destino}|({util.ahora()}) {self.nombre}: {mensaje_encriptado}"
                self.cliente.enviar(paquete)
        else:
            # Mensaje público
            mensaje_encriptado = encriptar.encriptar(texto)
            # Formato que espera el servidor TCP
            paquete = f"/PUBLICO|TODOS|({util.ahora()}) {self.nombre}: {mensaje_encriptado}"
            self.cliente.enviar(paquete)

        self.campo_entrada.delete(0, tk.END)

    def manejar_mensaje_entrante(self, mensaje):
        """
        Recibe un mensaje del hilo de red y lo pone en la cola de eventos
        de Tkinter para ser procesado de forma segura en el hilo principal de la GUI.
        """
        self.ventana_chat.after(0, self._procesar_mensaje_en_ui, mensaje)

    def _procesar_mensaje_en_ui(self, texto):
        """
        Se ejecuta en el hilo de la GUI.
        """
        print(f"DEBUG UI - Procesando: '{texto}'")
        
        # Manejar mensajes con formato /PUBLICO|... o /PRIVADO|...
        if texto.startswith("/PUBLICO|") or texto.startswith("/p|"):
            try:
                partes = texto.split("|", 2)
                if len(partes) == 3:
                    tipo = partes[0]  # /PUBLICO o /PRIVADO
                    destino = partes[1]  # TODOS o nombre destino
                    contenido = partes[2]  # (fecha) nombre: mensaje_encriptado
                    
                    # Extraer el mensaje encriptado
                    if ": " in contenido:
                        # Separar el prefijo (fecha) nombre: del mensaje encriptado
                        prefijo, encriptado = contenido.rsplit(": ", 1)
                        
                        try:
                            # Desencriptar el mensaje
                            desencriptado = encriptar.desencriptar(encriptado)
                            texto_mostrar = f"{prefijo}: {desencriptado}"
                            
                            # Mostrar como mensaje público normal
                            if "SERVIDOR" in prefijo:
                                self.mostrar_mensaje_sistema(desencriptado)
                            else:
                                # Extraer nombre del remitente
                                nombre_partes = prefijo.split(" ")
                                nombre = nombre_partes[-1] if nombre_partes else "Usuario"
                                self.mostrar_mensaje(nombre, desencriptado, 
                                                es_propio=(nombre == self.nombre))
                            return
                        except Exception as e:
                            print(f"Error al desencriptar: {e}")
                            self.mostrar_mensaje_sistema(contenido)
                            return
            except Exception as e:
                print(f"Error al procesar mensaje con pipe: {e}")
                self.mostrar_mensaje_sistema(texto)
                return
        
        # Mensaje privado (formato original sin pipes)
        if texto.startswith("(privado de") or texto.startswith("(privado para"):
            try:
                # Extraer info y el resto
                info, resto = texto.split(":", 1)
                resto = resto.strip()
                
                # Buscar el ÚLTIMO ": " para separar el mensaje encriptado
                if ": " in resto:
                    ultimo_dos_puntos = resto.rfind(": ")
                    prefijo = resto[:ultimo_dos_puntos]
                    encriptado = resto[ultimo_dos_puntos + 2:]
                    
                    # Desencriptar
                    try:
                        desencriptado = encriptar.desencriptar(encriptado)
                        mensaje_final = f"{prefijo}: {desencriptado}"
                    except:
                        mensaje_final = resto
                else:
                    mensaje_final = resto
                
                if info.startswith("(privado de"):
                    remitente = info.split(" ")[2].strip(")")
                    # Mostrar solo el mensaje desencriptado
                    self.mostrar_mensaje(remitente, f"→ {desencriptado}", es_privado=True)
                else:
                    destinatario = info.split(" ")[2].strip(")")
                    self.mostrar_mensaje(self.nombre, f"→ {destinatario}: {desencriptado}", 
                                    es_propio=True, es_privado=True)
                return
            except Exception as e:
                print(f"Error: {e}")
                self.mostrar_mensaje_sistema(texto)
                return

        # Mensaje del sistema (sin formato especial)
        if "se unió al chat" in texto or "dejó el chat" in texto:
            self.mostrar_mensaje_sistema(texto)
            return

        # Cualquier otro mensaje
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

        import datetime
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
