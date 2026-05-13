import hashlib as hash

""" 
Registro usuarios, 
el usuario es la llave 
la contraseña el valor

"""
usuarios  = {
    "aaron": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
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
        return False

    # hashear contraseña para comparar con los registros locales
    contrasenia_hasheada = hash.sha256(contrasenia.encode()).hexdigest()
    # devuelve true si coincide
    if usuarios[usuario] == contrasenia_hasheada:
        USUARIO = usuario
        return True

