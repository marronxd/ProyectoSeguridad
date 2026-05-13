from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

"""
Modulo que encripta y descencripta con AES-128 

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775

"""

# Auxiliares para encriptado y desencriptado
# La llave debe ser de 16 bytes para AES-128
LLAVE = b'PotrosItson12345' # 16 caracteres exactos
BLOCK_SIZE = 16
FORMATO = "utf-8"

def encriptar(mensaje):
    # 1.- Crear el objeto cifrador
    # COnfigura  el encriptado usando algoritmo AES con la llave y  reglas ECB
    # divide el texto en bloques de 16 bytes y los encripta independiente   
    cifrador = AES.new(LLAVE, AES.MODE_ECB)

    # 2.- Rellenar los bloques de 16 bytes y encriptar
    mensaje_relleno = pad(mensaje.encode(FORMATO), BLOCK_SIZE)
    mensaje_encriptado = cifrador.encrypt(mensaje_relleno) # encriptar

    # 3.- Transportarlo con base64 para que no se corrompa  en el transporte
    return base64.b64encode(mensaje_encriptado).decode(FORMATO)

def desencriptar(mensaje_encriptadob64):
    # 1.- Convertir de base64 a bytes encriptados
    mensaje_encriptado = base64.b64decode(mensaje_encriptadob64)

    # 2.- Crear el descifrador
    descifrador = AES.new(LLAVE, AES.MODE_ECB)

    # 3.- descencriotar  y removerle el relleno q le metió
    mensaje_relleno = descifrador.decrypt(mensaje_encriptado)
    mensaje_final = unpad(mensaje_relleno, BLOCK_SIZE)

    return mensaje_final.decode(FORMATO)