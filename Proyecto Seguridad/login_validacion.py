import hashlib as hash
import re  # regex
import utilerias as util

"""
Autores:
 @author Aaron Burciaga - 262788
 @author Brian Sandoval - 262741
 @author Dayanara Peralta - 262695
 @author María Valdez - 262775
"""

""" 
Registro usuarios, 
el usuario es la llave 
la contraseña el valor

"""
usuarios  = {
    "aaron": "6b51d431df5d7f141cbececcf79edf3dd861c3b4069f0b11661a3eefacbba918",
    "cachorrita123": "3c98379477063f2762283023e3f495570853f6696b9968a3560b3706080b0373"
    }

# la declaramos
USUARIO = None 

"""
 función que validar la identidad y acceso de un usuario.
"""
def validar_identidad (usuario, contrasenia):
    global USUARIO # para modificar la global
    # Regresa falso si no existe
    if usuario not in usuarios:
        util.guardar_log("Acceso con usuario inexistente", "warning")
        return False

    # hashear contraseña para comparar con los registros locales
    contrasenia_hasheada = hash.sha256(contrasenia.encode()).hexdigest()

    # devuelve true si coincide
    if usuarios[usuario] == contrasenia_hasheada:
        USUARIO = usuario
        return True
    util.guardar_log("Contrasenia incorrecta", "warning")




# se añadira para registrar usuario
""" funcion para validar el formato de la contraseña"""
def validar_formato(contrasenia):
    # patron que debe seguir la contrasenia
    patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

    # si el patron concuerda
    if re.match(patron, contrasenia):
        return True
    return False
