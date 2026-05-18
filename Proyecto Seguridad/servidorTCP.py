"""
servidorTCP.py

Descripción:
Se encarga de recibir los mensajes y ser quien dictamina a quién manda los mensajaes.
Controla el flujo de envío de mensajes. 
Maneja reglas de negocio que el servidor tiene.

Funciones principales:
    - iniciar()      -> Arranca el servidor
    - recibir()      -> Acepta nuevas conexiones
    - manejar()      -> Procesa mensajes de un cliente
    - mensaje_privado() -> Envía mensajes privados
    - transmitir_a_todos() -> Envía mensajes públicos

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

"""Importaciones"""
import threading
import socket
import queue
import utilerias as util
from cryptography.hazmat.primitives import serialization 
import  encriptar
import base64


"""
mensajes:
Cola para compartir mensajes entre hilos y que todos los puedan ver
en otras palabras, es la base del chat grupal.

bloqueo:
Se asegura que no modifiquen la variable varios hilos en simultaneo

condicion:
Hace que el hilo pueda usarse una vez sea liberado por un cliente
"""
mensajes = queue.Queue()
bloqueo = threading.Lock()
condicion = threading.Condition()

"""
Listas para guardar clientes y sus nombres

codigo: variable encargada de definir el tipo de decodificador
"""
clientes = []
nombres = []
llaves_publicas = {} #almacena las llaves publicas de los clientes
codigo = "UTF-8"

"""
Variable controladora de clientes activos en simultaneo
"""
CAPACIDAD_MAXIMA = 5
usuariosActivos = 0

# Generar par de llaves para el servidor
llave_privada_servidor, llave_publica_servidor = encriptar.generar_llaves()

"""
Función que da inicio al servidor
"""
def iniciar(puerto=51225):
    global servidor # Si no se hace global, se vuelve una variable local
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #El servidor es un socket TCP (SOCK_STREAM) IPv4 (AF_INET)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Asigna una configuracion general al socket(socket.SOL_SOCKET), dicha config hace que otro cliente reutilice el puerto, el 1 es para activar
    servidor.bind(("0.0.0.0", puerto)) #Se conecta: IP (localhost en este caso), puerto (51225 por el 05/12/25). Parámetro de tupla
    servidor.listen() #Espera y atiende los clientes. Tiene una lista de espera en el SO


    # Debugs solo para comprobar funcionamiento, se puede ignorar o eliminar
    print("DEBUG: El socket está abierto y escuchando en 0.0.0.0") 
    print(f"Servidor iniciado en puerto {puerto}")
    print("Abre varias terminales y ejecuta cliente.py")
    recibir()

"""
Se encarga de manejar  el envio de mensajes a todo el grupo
y a su vez se encarga de eliminar a participantes que abandonaron el chat
"""
def manejar(cliente):
    global usuariosActivos # Para que todo el módulo tenga acceso a ella

    indice = clientes.index(cliente)
    nombre_origen = nombres[indice] # Mediante el indice de cliente se accede al nombre del mismo

    try:
        while True:
            # Recibir mensaje

            datos = cliente.recv(4096) # Espera a recibir datos del cliente. Recibe bytes

            if not datos:
                util.guardar_log(f"Se desconectó", "info")
                break

            # Intentar decodificar como string primero (para detectar si es privado)
            try:

                mensaje_str = datos.decode(codigo)

                # Verificar si es mensaje privado (NO encriptado el envoltorio)
                if mensaje_str.startswith("/p|"):
                    partes = mensaje_str.split("|", 2)

                    if len(partes) == 3:
                        destino = partes[1]
                        contenido_b64 = partes[2]  # El contenido está en base64 para transportarlo sin que se corrompa

                        if destino == nombre_origen:
                            continue # No procesar si se manda mensaje a si mismo

                        mensaje_privado(cliente, destino, contenido_b64)
                        util.guardar_log(f"{nombre_origen} se comunicó en privado con: {destino}", "info")
                        continue # Si es privado se ignora lo demás
                continue

            except UnicodeDecodeError:
                # Los datos no son texto plano, intentar como encriptado (mensaje público)
                try:

                    mensaje_claro = encriptar.desencriptar(datos, llave_privada_servidor)
                    print(f"DEBUG - Mensaje desencriptado: {mensaje_claro[:50]}")

                    # Verificar si es mensaje privado en datos encriptados (no debería pasar)
                    if mensaje_claro.startswith("/p|"):
                        partes = mensaje_claro.split("|", 2)
                        if len(partes) == 3:
                            destino = partes[1]
                            contenido = partes[2]
                            if destino == nombre_origen:
                                continue
                            # Aquí el contenido ya viene en texto plano desde encriptación antigua
                            # Convertir a base64 para procesar
                            contenido_b64 = base64.b64encode(contenido.encode(codigo)).decode(codigo)
                            mensaje_privado(cliente, destino, contenido_b64)
                            continue

                    # Es mensaje público - enviar a CADA cliente encriptado con SU llave pública
                    for i, dest_socket in enumerate(clientes[:]): # [:] crea copia, enumerate extrae indice, valor
                        nombre_dest = nombres[i]
                        if nombre_dest == nombre_origen:
                            continue  # No enviar a sí mismo

                        # Obtener llave pública del destinatario
                        llave_dest_bytes = llaves_publicas.get(nombre_dest)
                        if llave_dest_bytes:
                            llave_dest = serialization.load_pem_public_key(llave_dest_bytes)
                            msg_encriptado = encriptar.encriptar(mensaje_claro, llave_dest)
                            dest_socket.send(msg_encriptado)

                except Exception as e:
                    print(f"Error desencriptando mensaje público: {e}")
                    continue

    except Exception as e:

        util.guardar_log(f"Error en manejar cliente: {e}", "error")
        # Si el socket se cierra o hay error de conexión, salimos para limpiar
        if isinstance(e, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, socket.error)):
            util.guardar_log(f"Error de conexión con {nombre_origen}: {e}", "error")
            pass # Solo no hace nada, se irá hacia el finally

        elif "decryption" in str(e).lower() or "decrypt" in str(e).lower() or "padding" in str(e).lower():
            util.guardar_log(f"Error de desencriptación con {nombre_origen}: {e}", "error")
            pass

        else:
            pass

    finally:
        limpiar_cliente(cliente) # Llama a la escoba gg

""""
    Limpia de los registros información de los clientes que dejan el servidor
    sin importar la razón. Disminuye el contador de usuarios. Elimina el socket
    de esa conexión junto con su nombre y llave pública. Además notifica al servidor
    la salida del mismo. Notifica a los demas clientes en espera que se liberó un 
    espacio para que puedan entrar al servidor.
"""

def limpiar_cliente(cliente):
    global usuariosActivos

    try:

        if cliente in clientes: # Busca el socket en la lista de sockets
            
            # Busca el cliente (socket) y lo elimina del registro
            # También extrae el nombre

            indice = clientes.index(cliente) # Cuando coincide, extrae el indice
            clientes.remove(cliente) # Remueve el socket de la lista
            nombre = nombres[indice] 
           
           # También elimina la llave del wey que se fue

            if nombre in llaves_publicas: # Cuando se lleva el nombre, se elimina su llave
                del llaves_publicas[nombre] # Borra la llave 
            cliente.close() # Cierra el socket y libera recursos
            
            # Recorre los nombres y también elimina el nombre del cliente que se fue

            if nombre in nombres:
                nombres.remove(nombre)
            transmitir_a_todos(f"{nombre} dejó el chat", nombre) # Avisa al chat
            usuariosActivos -= 1 # Disminuye los usuarios activos
           
           # Notifica al primer hilo en la cola que se liberó un espacio

            with condicion:
                condicion.notify() # Notifica
   
    except Exception as e:
        util.guardar_log(f"Error al limpiar cliente: {e}", "error")
        pass
    

"""
    Acepta los a los clientes al servidor y crea hilos que se asocian a cada cliente
    Esta función gestiona los hilos y a su vez asigna cada hilo a un cliente, añade cada cliente
    tanto como su nombre a registros y da avisos
"""

def recibir():
    global usuariosActivos, CAPACIDAD_MAXIMA
    while True:

        espera_turno() # Cuando entra un cliente, lo duerme si supera el max de activos
        cliente, direccion = servidor.accept() # Acepta la conexión y guarda el socket y su ip
        util.guardar_log(f"Cliente conectado desde: {direccion}", "info")
        
        # Enviar la clave pública del servidor al cliente
        try:
            
            # Configura y genera la llave pública del servidor

            llave_servidor_bytes = llave_publica_servidor.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Enviar tamaño de la llave (4 bytes) + la llave
            cliente.send(len(llave_servidor_bytes).to_bytes(4, 'big'))
            """
            Necesario para que el cliente sepa que es la llave del servidor y la lea como tal 
            y no como un mensaje normal. El 4 es porque independientemente siempre leerá 
            esos 4 bytes primero.
            """
            cliente.send(llave_servidor_bytes) 
        except Exception as e:
            util.guardar_log(f"{e}", "error")
            cliente.close() # Cierra el socket por si acaso
            continue
        
        # 2.- Pedir Handshake, el nombre del cliente al usuario
        cliente.send("Nombre: ".encode(codigo))
        respuesta = cliente.recv(4096).decode(codigo) # Traduce y escucha la respuesta del cliente
        
        # Extraer nombre
        try:
            """
            Esto estaba pensado para validar el formato del mensaje, contemplado en la
            primera versión de este proyecto. 
            Profe recuerde que solo 1/4 llevó Redes con usted. 
            """
            if "|" in respuesta: 
                partes = respuesta.split("|", 2)
                nombre = partes[2].strip() #sanitiza
            else:
                nombre = respuesta.strip()
        except Exception as e:
            util.guardar_log(f"Error de extraccion de nombre: {e}", "error")
            cliente.close() # Cerrar socket
            continue
        
        # Verificar si el nombre ya existe
        
        if usuario_repetido(cliente, nombre):
            util.guardar_log("Intento de conexión con la misma cuenta", "warning")
            continue
        
        # Recibir la llave pública del cliente
        
        try:
            # Recibir el tamaño de la llave (4 bytes)
            largo_llave_bytes = cliente.recv(4)

            if not largo_llave_bytes:
                raise Exception("No se recibió el tamaño de la llave") # El raise solo lanza excepción cuando quire
            largo_llave = int.from_bytes(largo_llave_bytes, 'big')
            
            # Recibir la llave pública
        
            llave_publica_bytes = cliente.recv(largo_llave)
            llaves_publicas[nombre] = llave_publica_bytes
            util.guardar_log(f"Llave pública recibida de {nombre}", "info")

        except Exception as e:
            util.guardar_log(f"Error al recibir llave pública de {nombre}: {e}", "error")
            cliente.close()
            continue
        
        # Agregar el cliente y su nombre a las listas
        nombres.append(nombre) 
        clientes.append(cliente)

        # Aviso de que alguien se unió
        mensaje_bienvenida = f'({util.ahora()}) SERVIDOR: {nombre} se unió al chat'
        util.guardar_log(f"Se unió al chat: {servidor}", "info")
        transmitir_a_todos(mensaje_bienvenida, nombre)

        cliente.send('Conectado al servidor ☻'.encode(codigo))
        
        # Enviar las llaves de los otros clientes al nuevo cliente

        try:

            for nombre_existente, llave_bytes in llaves_publicas.items():
                if nombre_existente != nombre:
                    # Enviar tamaño de la llave
                    cliente.send(len(llave_bytes).to_bytes(4, 'big'))
                    # Enviar la llave
                    cliente.send(llave_bytes)
                    # Enviar el nombre del dueño de la llave
                    nombre_bytes = nombre_existente.encode(codigo)
                    cliente.send(len(nombre_bytes).to_bytes(4, 'big'))
                    cliente.send(nombre_bytes)  # Enviar nombre

        except Exception as e:
            print(f"Error al enviar llaves de otros clientes: {e}")
        
        # Target indica la función que manejará el hilo
        # Args con quien trabajará, es decir, al cliente que se asocia
        hilo = threading.Thread(target=manejar, args=(cliente,)) # Se crea el hilo que conecta el servidor con el cliente
        with bloqueo: # Un hilo a la vez
            usuariosActivos += 1 # Modifica el contador
        hilo.start() # Empieza el hilo

"""
Busca si un nombre ya existe en el registro de nombres.
Cliente es el socket.
Nombre es el nombre de ese socket (o del usuario),

En caso de existir da retroalimentacion al cliente, cierra su socket,
Regresa verdadero.
Caso contrario, regresa falso.
"""
def usuario_repetido(cliente, nombre):
    if nombre in nombres:
        cliente.send("Nombre en uso, utilice otro usuario".encode(codigo))
        cliente.close()
        return True
    return False

"""
Envía mensaje solo a un cliente en específico.
Cliente es el socket.
Partes es el texto que recibe (ya decodificado) separado en partes.

En caso de haber excepción ValueError, notifica al usuario.
"""
def mensaje_privado(cliente, destino, contenido_b64):
    """
    Envía mensaje privado. El contenido viene en base64 (ya encriptado con llave del servidor).
    Aquí se desencripta, se re-encripta para el destinatario y se envía.
    """
    
    # Buscar el nombre del remitente usando el socket
    if cliente not in clientes:
        util.guardar_log("Cliente no encontrado en lista al intentar mensaje privado", "error")
        return
    indice_remitente = clientes.index(cliente)
    nombre_remitente = nombres[indice_remitente]
    
    # Obtener llave del remitente
    llave_remitente_bytes = llaves_publicas.get(nombre_remitente)
    if not llave_remitente_bytes:
        util.guardar_log(f"No se encontró la llave del remitente {nombre_remitente}", "error")
        return
    
    llave_remitente = serialization.load_pem_public_key(llave_remitente_bytes) # Carga la llave pública del remitente
    
    # Verificar si el destinatario existe
    if destino not in nombres:
        mensaje_error = f"SISTEMA: El usuario '{destino}' no está conectado."
        contenido_error_encriptado = encriptar.encriptar(mensaje_error, llave_remitente)
        contenido_error_b64 = base64.b64encode(contenido_error_encriptado).decode(codigo)
        resp_error = f"(privado para {destino}): {contenido_error_b64}"
        cliente.send(resp_error.encode(codigo))
        return
    
    # Obtener el socket y llave del destinatario
    indice_destino = nombres.index(destino)
    socket_destino = clientes[indice_destino]
    
    llave_dest_bytes = llaves_publicas.get(destino)
    if not llave_dest_bytes:
        util.guardar_log(f"No se encontró la llave del destinatario {destino}", "error")
        return
    llave_dest = serialization.load_pem_public_key(llave_dest_bytes) # Mismo proceso pero ahora con el destinatario
    
    # Desencriptar el contenido (viene en base64)
    contenido_bytes = base64.b64decode(contenido_b64.encode(codigo))
    contenido_claro = encriptar.desencriptar(contenido_bytes, llave_privada_servidor)
    
    # Enviar al destinatario
    contenido_encriptado_dest = encriptar.encriptar(contenido_claro, llave_dest)
    contenido_dest_b64 = base64.b64encode(contenido_encriptado_dest).decode(codigo)
    mensaje_receptor = f"(privado de {nombre_remitente}): {contenido_dest_b64}"
    socket_destino.send(mensaje_receptor.encode(codigo))
    
    # Enviar confirmación al remitente
    contenido_encriptado_rem = encriptar.encriptar(contenido_claro, llave_remitente)
    contenido_rem_b64 = base64.b64encode(contenido_encriptado_rem).decode(codigo)
    mensaje_emisor = f"(privado para {destino}): {contenido_rem_b64}"
    cliente.send(mensaje_emisor.encode(codigo))
    

"""
Pone al hilo en espera si este supera la capacidad máxima
"""
def espera_turno():
    with condicion: # Controla la cola de espera
        if usuariosActivos >= CAPACIDAD_MAXIMA:  
            condicion.wait() # Pone el hilo a esperar
    return

""" 
    Usado para la comunicación con todos los participantes del chat grupal, es decir, 
    enviar mensaje a todos los clientes. Transmite el contenido del mensaje encriptado
    con la llave pública de cada destinatario para que solo él pueda leerlo.
"""
def transmitir_a_todos(mensaje_str, remitente_nombre=None):

    for i, cliente_destino in enumerate(clientes[:]): # Extrae índice y socket
      
        nombre_destino = nombres[i] # Extrae nombre

        if remitente_nombre and nombre_destino == remitente_nombre:
            continue
        
        try:

            llave_bytes = llaves_publicas.get(nombre_destino)

            if llave_bytes:
                llave_destino = serialization.load_pem_public_key(llave_bytes)
                # En este punto mensaje_str ya es String, no hay que decodificar
                mensaje_encriptado = encriptar.encriptar(mensaje_str, llave_destino)
                cliente_destino.send(mensaje_encriptado)

            else:
                # Si no hay llave, enviar como bytes (texto plano), sirve para los mensjes
                # de sistema
                cliente_destino.send(mensaje_str.encode(codigo))

        except Exception as e:
            print(f"Error al transmitir a {nombre_destino}: {e}")

if __name__ == "__main__":
    iniciar(51225)
