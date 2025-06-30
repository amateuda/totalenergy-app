import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # Importa para manejar contraseñas

app = Flask(__name__)

# --- Configuración de la base de datos ---
# Render (producción) usará la variable de entorno DATABASE_URL.
# Para desarrollo local, si no tienes PostgreSQL local, puedes usar SQLite (sqlite:///site.db).
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Configuración de la SECRET_KEY ---
# Usa la variable de entorno SECRET_KEY de Render.
# En local, si no está configurada, usará la clave por defecto.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_secreta_super_segura_aqui_cambiala_en_produccion')

# --- Definir el modelo de la tabla Obras ---
class Obra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_obra = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    porcentaje_avance = db.Column(db.Integer, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Obra {self.nombre_obra} - {self.estado}>"

# --- Definir el modelo de la tabla Usuarios ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # Longitud AUMENTADA a 255 para el hash de contraseña

    def set_password(self, password):
        # Hashea la contraseña para guardarla de forma segura
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Verifica si la contraseña proporcionada coincide con la hasheada
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

# --- CREACIÓN DE TABLAS EN LA BASE DE DATOS (PARA PRODUCCIÓN EN RENDER) ---
# Este bloque se ejecutará CADA VEZ que la aplicación se inicie en Render.
# Se usó para la creación INICIAL de tablas.
# ¡IMPORTANTE!: Dado que las tablas 'obras' y 'user' ya se crearon con éxito
# en Render, COMENTAMOS esta línea para evitar problemas en futuras actualizaciones de esquema.
# Para cambios en el esquema en un proyecto real, se usarían migraciones (Flask-Migrate).
with app.app_context():
    # db.create_all() # ¡COMENTADO! Las tablas ya están creadas y configuradas correctamente.
    pass


# --- Rutas de la aplicación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # En una aplicación real, aquí configurarías una sesión para el usuario (ej. Flask-Login)
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verificar si el nombre de usuario ya existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('El nombre de usuario ya existe. Por favor, elige otro.', 'danger')
        else:
            new_user = User(username=username)
            new_user.set_password(password) # Hashea y guarda la contraseña
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado con éxito! Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    # En una aplicación real, aquí verificarías si el usuario está logueado
    obras = Obra.query.all()
    return render_template('dashboard.html', obras=obras)

@app.route('/add_obra', methods=['GET', 'POST'])
def add_obra():
    # Por ahora, esta ruta no está protegida, pero lo estará más adelante con el sistema de login
    if request.method == 'POST':
        nombre = request.form['nombre_obra']
        estado = request.form['estado']
        porcentaje = request.form.get('porcentaje_avance')
        observaciones = request.form.get('observaciones')

        if porcentaje:
            try:
                porcentaje = int(porcentaje)
            except ValueError:
                porcentaje = None
        else:
            porcentaje = None

        nueva_obra = Obra(
            nombre_obra=nombre,
            estado=estado,
            porcentaje_avance=porcentaje,
            observaciones=observaciones
        )
        db.session.add(nueva_obra)
        db.session.commit()
        flash('Obra añadida con éxito!', 'success') # Mensaje de éxito
        return redirect(url_for('dashboard'))
    return render_template('add_obra.html')

# --- Bloque de ejecución principal para desarrollo local ---
if __name__ == '__main__':
    app.run(debug=True)