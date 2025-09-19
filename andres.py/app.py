from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Cambia si tienes contraseña
app.config['MYSQL_DB'] = 'usuariosdb'

mysql = MySQL(app)
login_manager = LoginManager(app)

class Usuario(UserMixin):
    def __init__(self, id, nombre, correo, edad, contraseña):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.edad = edad
        self.contraseña = contraseña

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return Usuario(user[0], user[1], user[2], user[3], user[4])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        edad = request.form['edad']
        contraseña = request.form['contraseña']
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO usuarios (nombre, correo, edad, contraseña) VALUES (%s, %s, %s, %s)", (nombre, correo, edad, contraseña))
            mysql.connection.commit()
            flash('Usuario registrado correctamente')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error: el correo ya está registrado')
        finally:
            cur.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE correo = %s AND contraseña = %s", (correo, contraseña))
        user = cur.fetchone()
        cur.close()
        if user:
            usuario = Usuario(user[0], user[1], user[2], user[3], user[4])
            login_user(usuario)
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos')
    return render_template('login.html')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/catalogo')
@login_required
def catalogo():
    return render_template('catalogo.html')
@app.route('/editar_usuario', methods=['GET', 'POST'])
@login_required
def editar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        edad = request.form['edad']
        contraseña = request.form['contraseña']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE usuarios SET nombre = %s, correo = %s, edad = %s, contraseña = %s WHERE id = %s
        """, (nombre, correo, edad, contraseña, current_user.id))
        mysql.connection.commit()
        cur.close()
        flash('Usuario actualizado correctamente')
        return redirect(url_for('dashboard'))
    return render_template('editar_usuario.html', usuario=current_user)
@app.route('/eliminar_usuario', methods=['GET', 'POST'])
@login_required
def eliminar_usuario():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s", (current_user.id,))
        mysql.connection.commit()
        cur.close()
        flash('Tu cuenta ha sido eliminada correctamente.')

        # Cierra la sesión del usuario eliminado
        logout_user()
        return redirect(url_for('login'))

    return render_template('eliminar_usuario.html', usuario=current_user)

if __name__ == '__main__':
    app.run(debug=True)