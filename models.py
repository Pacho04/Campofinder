from flask_login import UserMixin

# ---- Modelo Usuario (para Flask-Login) ----
class User(UserMixin):
    def __init__(self, id, correo, nombre=None, rol=None):
        self.id = id
        self.correo = correo
        self.nombre = nombre
        self.rol = rol

    def __repr__(self):
        return f"<User {self.correo} - Rol: {self.rol}>"


# ---- Modelo Reserva ----
class Reserva:
    def __init__(self, id_reserva, id_usuario, cancha, horario, fecha):
        self.id_reserva = id_reserva
        self.id_usuario = id_usuario
        self.cancha = cancha
        self.horario = horario
        self.fecha = fecha

    def __repr__(self):
        return f"<Reserva {self.id_reserva} - Usuario {self.id_usuario} - Cancha {self.cancha}>"


# ---- Modelo Cancha ----
class Cancha:
    def __init__(self, id_cancha, nombre, ubicacion, tipo):
        self.id_cancha = id_cancha
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.tipo = tipo

    def __repr__(self):
        return f"<Cancha {self.nombre} ({self.tipo})>"
