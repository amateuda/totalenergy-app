from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

# Configuración de la clave secreta
# Usa una variable de entorno en producción por seguridad
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_secreta_super_segura_aqui_cambiala_en_produccion')

# Configuración de la base de datos
# Esta es la URL de tu base de datos de Render que me has proporcionado
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://total_energy_db_render_user:2y4hvan5Xcrb0jpvhTJ2Wehl6Nuld8P4@dpg-d1h1v57gi27c73c74000-a.oregon-postgres.render.com/total_energy_db_render'

# Desactiva el seguimiento de modificaciones de SQLAlchemy para ahorrar recursos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Definición del modelo de usuario para la base de datos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"

# Mover db.create_all() aquí, fuera del if __name__ == '__main__':
# Esto asegura que las tablas se creen cuando Gunicorn carga la aplicación en Render.
with app.app_context():
    db.create_all()

# Rutas de la aplicación
@app.route('/')
def home():
    return render_template('index.html', title='Inicio')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor, ingresa un nombre de usuario y una contraseña.', 'danger')
            return render_template('register.html', title='Registrarse')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado con éxito! Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() # En caso de error, deshaz la transacción
            # Verifica si es un error de duplicado (ej. nombre de usuario ya existe)
            if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                flash('El nombre de usuario ya existe. Por favor, elige otro.', 'danger')
            else:
                flash(f'Ocurrió un error al registrar el usuario: {e}', 'danger')
            return render_template('register.html', title='Registrarse')

    return render_template('register.html', title='Registrarse')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard')) # Redirige al dashboard o a donde sea necesario
        else:
            flash('Inicio de sesión fallido. Por favor, verifica tu usuario y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión')

@app.route('/dashboard')
def dashboard():
    # Esta es una ruta de ejemplo para después del inicio de sesión
    return render_template('dashboard.html', title='Dashboard')


# El bloque if __name__ == '__main__': ahora solo correrá la app localmente,
# ya no necesita crear las tablas porque eso ya se hace arriba.
if __name__ == '__main__':
    app.run(debug=True) # debug=True para desarrollo, ponlo en False para producción