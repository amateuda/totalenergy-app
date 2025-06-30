import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_secreta_super_segura_aqui')

# --- Definir el modelo de la tabla Obras ---
# Esta clase representa la tabla 'obras' en tu base de datos.
class Obra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_obra = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False) # 'En proceso' o 'Finalizada'
    porcentaje_avance = db.Column(db.Integer, nullable=True) # Solo si 'En proceso', puede ser nulo
    observaciones = db.Column(db.Text, nullable=True) # Puede ser nulo

    def __repr__(self):
        return f"<Obra {self.nombre_obra} - {self.estado}>"

# --- CREACIÓN DE TABLAS EN LA BASE DE DATOS ---
# Este bloque se ejecutará CADA VEZ que la aplicación se inicie en Render (o localmente).
# Es útil para la creación inicial de tablas en la versión gratuita de Render.
# ¡IMPORTANTE!: Después de que la tabla 'obras' se haya creado con éxito en Render y hayas cargado datos de prueba,
# COMENTA O ELIMINA este bloque para evitar problemas en futuras actualizaciones de esquema.
with app.app_context():
    db.create_all() # Esto creará la tabla 'obras' si no existe.

# --- Rutas de la aplicación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Aquí irá la lógica de autenticación más adelante
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Obtiene todas las obras de la base de datos para mostrarlas
    obras = Obra.query.all()
    return render_template('dashboard.html', obras=obras)

@app.route('/add_obra', methods=['GET', 'POST'])
def add_obra():
    if request.method == 'POST':
        # Recoge los datos del formulario
        nombre = request.form['nombre_obra']
        estado = request.form['estado']
        porcentaje = request.form.get('porcentaje_avance')
        observaciones = request.form.get('observaciones')

        # Procesa el porcentaje, asegurándose de que sea entero o None
        if porcentaje:
            try:
                porcentaje = int(porcentaje)
            except ValueError:
                porcentaje = None
        else:
            porcentaje = None

        # Crea una nueva instancia de Obra y la guarda en la base de datos
        nueva_obra = Obra(
            nombre_obra=nombre,
            estado=estado,
            porcentaje_avance=porcentaje,
            observaciones=observaciones
        )
        db.session.add(nueva_obra)
        db.session.commit()
        return redirect(url_for('dashboard')) # Redirige al dashboard después de guardar
    return render_template('add_obra.html') # Muestra el formulario para añadir obra

# --- Bloque de ejecución principal para desarrollo local ---
if __name__ == '__main__':
    # Cuando ejecutas 'python app.py' localmente.
    # La llamada a db.create_all() que está arriba ya se encargará de crear la tabla.
    app.run(debug=True) # Inicia el servidor de desarrollo en modo depuración