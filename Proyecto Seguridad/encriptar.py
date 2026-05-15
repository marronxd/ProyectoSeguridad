

"""Librerias para ejecutar la descarga"""
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

"""
Modulo que encripta y descencripta con RSA-128 

Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775

"""

FORMATO = "utf-8"

"""
 Generar las llaves publica y privada por cada cliente que abra el chat. Solo la primera vez
 """
def generar_llaves():
    llave_privada = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    llave_publica = llave_privada.public_key()
    return llave_privada, llave_publica

"""Encripta para envio. Requiere la llave publica para poder descifrar el mensaje"""

def encriptar(mensaje, llave_publica_receptor):
    return llave_publica_receptor.encrypt(
        mensaje.encode(FORMATO), #convertir a cadnea de bits
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), # padding para que no sea determinista.  el MGF1 revuelve los bits para que no pueda ser predecible
            algorithm=hashes.SHA256(), # por si se llegase a modificar, ya no es el mismo hash
            label=None
        )
    )

"""Desencripta el mensaje que se recibe. Requiere la llave privada para desbloquearlo"""
def desencriptar(mensaje_cifrado, llave_privada_propia):
    return llave_privada_propia.decrypt(
        mensaje_cifrado,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode(FORMATO)










"""AUxiliar para descargar la libreria de encriptado"""
def instalar_dependencias():
    try:
        # Intentamos importar la librería
        import cryptography
        print("Librería 'cryptography' ya está instalada.")
    except ImportError:
        # Si no existe, Python ejecuta el comando de instalación
        print("Instalando la librería 'cryptography' necesaria para RSA...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        print("Instalación completada con éxito.")

# Llamamos a la función antes de cualquier otra cosa
instalar_dependencias()


if __name__ == "__main__":
    instalar_dependencias()