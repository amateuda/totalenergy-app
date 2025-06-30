import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Configuración de la base de datos ---
# En Render (producción), usaremos la variable de entorno DATABASE_URL que ya configuraste.
# Para desarrollo local, puedes usar una base de datos SQLite temporal si no tienes PostgreSQL local configurado,
# o una configuración de PostgreSQL local si la tienes.
# La línea 'os.environ.get('DATABASE_URL')' intentará obtener la URL de Render,
# si no la encuentra (porque estás localmente), usará lo que pongas después del ','.
# Por ejemplo, para desarrollo local con SQLite (más sencillo de iniciar):
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
# Si tienes PostgreSQL local y quieres usarlo, podrías poner algo como:
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/dbname')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado para evitar warnings de SQLAlchemy

db = SQLAlchemy(app)

# --- Configuración de la SECRET_KEY ---
# Usa la variable de entorno SECRET_KEY que ya configuraste en Render.
# Si no la encuentra (ej. en desarrollo local sin configurar la variable), usará la clave por defecto.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_secreta_super_segura_aqui')

# --- Definir el modelo de la tabla Obras ---
# Esta clase representa la tabla 'obras' en tu base de datos PostgreSQL.
class Obra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_obra = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False) # 'En proceso' o 'Finalizada'
    porcentaje_avance = db.Column(db.Integer, nullable=True) # Solo si 'En proceso', puede ser nulo
    observaciones = db.Column(db.Text, nullable=True) # Puede ser nulo

    def __repr__(self):
        # Representación amigable para depuración
        return f"<Obra {self.nombre_obra} - {self.estado}>"

# --- Rutas de la aplicación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Por ahora, solo muestra la plantilla de login. La lógica de autenticación se añadiría aquí.
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Recupera todas las obras de la base de datos
    obras = Obra.query.all()
    # Pasa la lista de obras a la plantilla 'dashboard.html' para que se muestren
    return render_template('dashboard.html', obras=obras)

# --- Ruta para agregar nuevas obras (temporal y para prueba) ---
# Esta ruta permitirá añadir datos a tu tabla 'obras'.
# En un sistema real, esta ruta estaría protegida por autenticación y/o roles de usuario.
@app.route('/add_obra', methods=['GET', 'POST'])
def add_obra():
    if request.method == 'POST':
        # Si la solicitud es POST, el usuario envió el formulario
        nombre = request.form['nombre_obra']
        estado = request.form['estado']
        porcentaje = request.form.get('porcentaje_avance') # Usar .get() para campos opcionales
        observaciones = request.form.get('observaciones')

        # Convertir porcentaje a entero si se proporcionó, si no, dejarlo como None
        if porcentaje:
            try:
                porcentaje = int(porcentaje)
            except ValueError:
                porcentaje = None # Si no es un número válido, lo dejamos nulo
        else:
            porcentaje = None

        # Crea una nueva instancia de la Obra con los datos del formulario
        nueva_obra = Obra(
            nombre_obra=nombre,
            estado=estado,
            porcentaje_avance=porcentaje,
            observaciones=observaciones
        )
        # Añade la nueva obra a la sesión de la base de datos y guarda los cambios
        db.session.add(nueva_obra)
        db.session.commit()
        # Redirige al usuario al dashboard para que vea la obra añadida
        return redirect(url_for('dashboard'))
    # Si la solicitud es GET, simplemente muestra el formulario para añadir una obra
    return render_template('add_obra.html')


# --- Bloque de ejecución principal cuando el script se corre directamente ---
if __name__ == '__main__':
    # 'with app.app_context():' es crucial para que SQLAlchemy sepa a qué aplicación Flask pertenece 'db'.
    # db.create_all() crea las tablas en la base de datos si aún no existen.
    # Esto es útil para desarrollo local. En Render, lo haremos manualmente una vez en la Shell.
    with app.app_context():
        db.create_all()
    app.run(debug=True) # Inicia el servidor de desarrollo de Flask