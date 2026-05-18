"""
clienteTCP.py

Descripción:
- Utiliza sockets e hilos para comunicarse a un servidor de protocolo TCP codificando con ASCII
- Los parámetros los recibe con los datos recolectados de conectar.py

Funcionamiento:
- Importa sockets e hilos
- iniciar(): llama a las funciones internos, recibe 'mostrar_funcion' como parámetro
- conectar(): configura la conexión del cliente, que es un socket (IP y puerto)
- recibir(): recibe instrucciones y mensajes del servidor y usa 'mostrar_funcion' para imprimir
- escribir(): envía mensajes al servidor junto con nombre de usuario y la fecha y hora
- hilosCliente(): ejecuta las funciones en hilos

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

"""Importaciones"""
import socket       # Conecta dispositivos mediante cliente-servidor
import threading    # Ejecuta paralelamente
import utilerias as util  # Funciones varias
import encriptar  # modulo de encriptado y desencriptado
from cryptography.hazmat.primitives import serialization

"""Encapsula todo en una función para llamarla desde menu.py"""
def iniciar(mostrar_funcion):
    ip = util.pedirIp()
    puerto = util.pedirPuerto()
    nombre = util.pedirNombre()
    cliente = conectar(ip, puerto)  # Establece la conexión con el servidor
    
    # Generar llaves propias
    llave_privada, llave_publica = encriptar.generar_llaves()
    
    # Handshake
    handshake(cliente, nombre, llave_publica)
    
    hilosCliente(recibir, escribir, cliente, nombre, mostrar_funcion, llave_privada)  # Llama la función que ejecuta hilos
    return cliente


"""Configura el cliente mediante un socket"""
def conectar(ip, puerto):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket TCP (SOCK_STREAM) IPv4 (AF_INET)
    cliente.settimeout(5)  # Tiempo máximo de espera 5 segundos
    try:
        cliente.connect((ip, puerto))  # Se conecta con el servidor una vez y queda asociado.
    except socket.timeout:
        raise Exception(f"Timeout: No se pudo conectar al servidor TCP en {ip}:{puerto}")
    except ConnectionRefusedError:
        raise Exception(f"Conexión rechazada: No hay servidor TCP escuchando en {ip}:{puerto}")
    except socket.gaierror:
        raise Exception(f"Error de DNS: No se pudo resolver la dirección {ip}")
    except Exception as e:
        raise Exception(f"No se pudo conectar: {e}")
    finally:
        cliente.settimeout(None)  # Restaura el timeout a infinito después de conectar
    return cliente

"""Realiza el handshake inicial con el servidor"""
def handshake(cliente, nombre, llave_publica):
    # Recibir llave pública del servidor
    llave_publica_servidor_bytes = cliente.recv(4096)
    llave_publica_servidor = serialization.load_pem_public_key(llave_publica_servidor_bytes)
    
    # Recibir "Nombre: "
    paquete = cliente.recv(4096).decode(util.codigo)
    if paquete == "Nombre: ":
        cliente.send(nombre.encode(util.codigo))
    
    # Recibir "Llave: "
    paquete = cliente.recv(4096).decode(util.codigo)
    if paquete == "Llave: ":
        llave_publica_serializada = llave_publica.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        cliente.send(llave_publica_serializada)
    
    # Aquí podría recibir llaves de otros clientes, pero por simplicidad, omitir

"""Recibe mensajes del servidor TCP"""
def recibir(cliente, nombre, mostrar_funcion, llave_privada):
    while True:
        try:
            paquete = cliente.recv(4096).decode(util.codigo)  # Mensaje decodificado
            
            if not paquete:
                continue
            else:
                if ": " in paquete:
                    try:
                        # Cortamos en el ÚLTIMO ": " para obtener el mensaje encriptado
                        prefijo, contenido_encriptado = paquete.rsplit(": ", 1)
                        
                        # Desencriptamos
                        contenido_claro = encriptar.desencriptar(contenido_encriptado.encode(util.codigo), llave_privada)
                        
                        texto_para_mostrar = f"{prefijo}: {contenido_claro}"
                    except Exception:
                        # Si falla (ej. mensaje del sistema no encriptado), mostramos original
                        texto_para_mostrar = paquete
                else:
                    # Mensajes directos del servidor sin formato ": "
                    texto_para_mostrar = paquete
                print(f"recibir cliente tcp . Texto: {texto_para_mostrar}")
                mostrar_funcion(texto_para_mostrar)  # *** USO DE LA FUNCIÓN PASADA COMO PARÁMETRO ***
        except Exception as e:
            mostrar_funcion(f"Error: {e}")  # Usamos también la función para mostrar el error
            cliente.close()  # Si hay un error, cierra el cliente y rompe el bucle
            break


"""Envía mensajes al servidor TCP"""
def escribir(cliente, nombre, llave_publica_servidor):
    while True:
        texto = input("")  # Contenido del mensaje

        if texto.startswith("/p "):

            # Para mensaje privado

            partes = texto.split(" ", 2)
            destino = partes[1]
            contenido = partes[2]

            # Se encripta solo el contenido
            mensaje_encriptado = encriptar.encriptar(contenido, llave_publica_servidor)

            # Armado del paquete
            paquete = f"/p|{destino}|({util.ahora()}) {nombre}: {mensaje_encriptado}"

        else: # Mensajes públicos 
            mensaje_encriptado = encriptar.encriptar(texto, llave_publica_servidor)

            # Armar paquete

            paquete = f"/PUBLICO|TODOS|({util.ahora()}) {nombre}: {mensaje_encriptado}"  # Mensaje con emisor y fecha
        cliente.send(paquete.encode(util.codigo))  # Codifica dicho mensaje con utf-8


"""Inserta los métodos en hilos e inicia su funcionamiento con .start()"""
def hilosCliente(recibir, escribir, cliente, nombre, mostrar_funcion, llave_privada, llave_publica_servidor):
    # Se agrega 'mostrar_funcion' a los argumentos de 'recibir'
    threading.Thread(target=recibir, args=(cliente, nombre, mostrar_funcion, llave_privada)).start()
    threading.Thread(target=escribir, args=(cliente, nombre, llave_publica_servidor)).start()


# NOTA: La llamada final a iniciar() DEBE ser modificada por el usuario al usar este archivo.
# Por ejemplo, si se usa desde otro script (como menu.py), el archivo lo llamaría así:
# cliente_tcp.iniciar(print)
#
# Para que funcione al ejecutar este archivo directamente:
def funcion_para_mostrar(texto):
    print(texto)


if __name__ == "__main__":
    iniciar(funcion_para_mostrar)
