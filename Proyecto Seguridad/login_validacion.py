"""Importaciones"""
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
    "cachorrita123": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "Brian": "f3fe5a51a2be8c6dc715028858fcba82ee021be7687e4f95b45086b8ffb1a23f",
    "Dayanara": "944c27e5b97ab7793e4b6e9ff29384890ece0c7c04d2e2bf81c5f763469cc66b",
    "Maria": "6d1770695e81c6e1107cd5eed4954828f52abba7c830059edf16926b73d66bd2"
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

    # Hashear contraseña para comparar con los registros locales
    contrasenia_hasheada = hash.sha256(contrasenia.encode()).hexdigest()

    # Devuelve true si coincide
    if usuarios[usuario] == contrasenia_hasheada:
        USUARIO = usuario
        return True
    util.guardar_log("Contrasenia incorrecta", "warning")


# Se añadirá para registrar usuario
""" función para validar el formato de la contraseña"""
def validar_formato(contrasenia):
    # Patrón que debe seguir la contrasenia
    patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

    # Si el patron concuerda
    if re.match(patron, contrasenia):
        return True
    return False
