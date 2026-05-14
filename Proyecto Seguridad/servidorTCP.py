"""
servidorTCP.py

Descripción:
-

Funcionamiento:

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
"""Configura el servidor mediante un socket
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #El servidor es un socket TCP (SOCK_STREAM) IPv4 (AF_INET)
servidor.bind(("127.0.0.1", 51225)) #Se conecta: IP (localhost en este caso), puerto (51225 por el 05/12/25). Parámetro de tupla
servidor.listen() #Espera mensajes de clientes
"""
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
codigo = "UTF-8"

"""
Variable controladora de clientes activos en simultaneo
"""
CAPACIDAD_MAXIMA = 1
usuariosActivos = 0

"""
funcion que da inicio al servidor
"""
def iniciar(puerto=51225):
    global servidor # Si no se hace global, se vuelve una variable local
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #El servidor es un socket TCP (SOCK_STREAM) IPv4 (AF_INET)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # asigna una configuracion general al socket(socket.SOL_SOCKET), dicha config hace que otro cliente reutilice el puerto, el 1 es para activar
    servidor.bind(("0.0.0.0", puerto)) #Se conecta: IP (localhost en este caso), puerto (51225 por el 05/12/25). Parámetro de tupla
    servidor.listen() #Espera y atiende los clientes. Tiene una lista de espera en el SO
    print("DEBUG: El socket está abierto y escuchando en 0.0.0.0") # <--- AÑADE ESTO
    print(f"Servidor iniciado en puerto {puerto}")
    print("Abre varias terminales y ejecuta cliente.py")
    recibir()


"""
Itera en la lista de todos los participantes para enviarles el mensaje que un cliente escribió
al resto de clientes en el server
"""
def transmitir(mensaje):
    print(f"Debug ->  Transmitiendo a {len(clientes)} clientes: {mensaje[:50]}...")
    for cliente in clientes[:]: 
        try:
            cliente.send(mensaje) #manda el mensaje de cada cliente
        except: #si un cliente es sacado por nombre repetido evita que truene
           # cliente.remove()
           # cliente.close()
            pass


"""
Se encarga de manejar  el envio de mensajes a todo el grupo
y a su vez se encarga de eliminar a participantes que abandonaron el chat
"""
def manejar(cliente):
    global usuariosActivos
    while True:
        try:
            mensaje = cliente.recv(1024)
            
            if not mensaje:
                break
                
            mensaje_str = mensaje.decode(codigo)
            print(f"Mensaje recibido: {mensaje_str}")  # Debug
            
            # Verificar si es mensaje privado
            if mensaje_str.startswith("/p|"):
                partes = mensaje_str.split("|", 2)
                if len(partes) == 3:
                    tipo = partes[0]
                    destino = partes[1]
                    contenido = partes[2]
                    mensaje_privado(cliente, destino, contenido)
                continue
            
            # Mensaje público - retransmitir a TODOS los clientes
            # IMPORTANTE: Enviar el mensaje original SIN MODIFICAR
            transmitir(mensaje)  # Esto envía los bytes originales
            
        except Exception as e:
            print(f"Error en manejar: {e}")
            break
    
    # Limpiar al desconectarse
    try:
        indice = clientes.index(cliente)
        clientes.remove(cliente)
        cliente.close()
        nombre = nombres[indice]
        transmitir(f"{nombre} dejó el chat".encode(codigo))
        nombres.remove(nombre)
        usuariosActivos -= 1
        with condicion:
            condicion.notify()
    except:
        pass                 #despierta un cliente en espera

    

"""
    Acepta los a los clientes al servidor y crea hilos que se asocian a cada cliente
    Esta funcion gestiona los hilos y a su vez asigna cada hilo a un cliente, añade cada cliente
    tanto como su nombre a registros y da avisos
"""

def recibir():
    global usuariosActivos, CAPACIDAD_MAXIMA
    while True:
        espera_turno()
        cliente, direccion = servidor.accept() #Acepta a los clientes al servidor  cliente guarda el socket, direccion la tupla de ip y puerto efimero
        
        print(f"Conectados con {str(direccion)}") #Muestra quién se conectó
        
        cliente.send("Nombre: ".encode(codigo)) #codifica el nombre del cliente
        respuesta = cliente.recv(1024).decode(codigo) #decodifica la respuesta del cliente

        try:
            # --- Lógica de extracción de nombre robusta ---
            if "|" in respuesta:
                # Si el cliente ya usa el nuevo formato de paquetes
                partes = respuesta.split("|", 2)
                nombre = partes[2].strip()
            else:
                # Si el cliente envía el nombre directo (Handshake simple)
                nombre = respuesta.strip()
            
        except Exception as e:
            print(f"Error al procesar nombre de {direccion}: {e}")
            cliente.close()
            continue

        if usuario_repetido(cliente, nombre):    #verifica si el nombre ya existe
            continue # ignora lo de abajo
        
        nombres.append(nombre) # agrega el nombre al registro de nombres
        clientes.append(cliente) # agrega al cliente al registro de clientes
        
        print(f'El nombre del cliente es {nombre}')

        # aviso de que alguien se unió
        transmitir(f'({util.ahora()}) SERVIDOR: {nombre} se unió al chat'.encode(codigo))   
        
        # Si tienes la función de log activa:
        # util.guardar_log(f"{nombre} se unió al servidor", "info") 
        
        cliente.send('Conectado al servidor ☻'.encode(codigo))
        
        # target indica la funcion que manejará el hilo
        # args con quien trabajara, es decir, al cliente que se asocia
        hilo = threading.Thread(target=manejar, args=(cliente,)) #se crea el hilo que conecta el servidor con el cliente
        with bloqueo: # un hilo a la vez
            usuariosActivos += 1 # modifica el contador
        hilo.start() # empieza el hilo




"""
Busca si nombre un nombre ya existe en el registro de nombres
cliente es el socket
nombre es el nombre de ese socket (o del usuario)

en caso de existir da retroalimentacion al cliente, cierra su socket
regresa verdadero
caso contrario, regresa falso
"""
def usuario_repetido(cliente, nombre):
    if nombre in nombres:
        cliente.send("Nombre en uso, utilice otro usuario".encode(codigo))
        cliente.close()
        return True
    return False

"""
Envía mensaje solo a un cliente en específico
cliente es el socket
partes es el texto que recibe (ya decodificado) separado en partes

en caso de haber excepcion ValueError, notifica al usuario
"""
def mensaje_privado(cliente, destino, contenido):
    try:
        # Buscar el nombre del remitente usando el socket
        if cliente not in clientes:
            return
        indice_remitente = clientes.index(cliente)  # ✅ Usar clientes, no nombres
        nombre_remitente = nombres[indice_remitente]
        
        # Verificar si el destinatario existe
        if destino not in nombres:
            cliente.send(f"SISTEMA: El usuario '{destino}' no está conectado.".encode(codigo))
            return
        
        # Obtener el socket del destinatario
        indice_destino = nombres.index(destino)
        socket_destino = clientes[indice_destino]  # ✅ Este es el socket real
        
        # Enviar mensaje al destinatario
        mensaje_receptor = f"(privado de {nombre_remitente}): {contenido}".encode(codigo)
        socket_destino.send(mensaje_receptor)
        
        # Enviar confirmación al remitente
        mensaje_emisor = f"(privado para {destino}): {contenido}".encode(codigo)
        cliente.send(mensaje_emisor)
        
    except Exception as e:
        print(f"Error en mensaje_privado: {e}")
        try:
            cliente.send(f"SISTEMA: Error al enviar mensaje privado".encode(codigo))
        except:
            pass
    

"""
pone al hilo en espera si este supera la capacidad maxima
"""
def espera_turno():
    with condicion: # controla la cola de espera
        if usuariosActivos >= CAPACIDAD_MAXIMA:  
            condicion.wait() #pone el hilo a esperar
    return


if __name__ == "__main__":
    iniciar(51225)
