from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
import secrets
from datetime import datetime

app = Flask(__name__)

# Configuración de la clave secreta
# Usa una variable de entorno en producción por seguridad
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

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

# Definición del modelo para Obras
class Obra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_obra = db.Column(db.String(120), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True) # Clave foránea
    estado = db.Column(db.String(50), nullable=False, default='En proceso')
    porcentaje_avance = db.Column(db.Integer, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref='obras', lazy=True) # Relación con Cliente
    historial_avance = db.relationship('HistorialAvance', backref='obra', lazy=True, cascade='all, delete-orphan')
    documentos = db.relationship('Documento', backref='obra', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Obra('{self.nombre_obra}', '{self.estado}')"

# Definición del modelo para Clientes
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(120), unique=True, nullable=False)
    cuit = db.Column(db.String(20), unique=True, nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    contacto_principal = db.Column(db.String(120), nullable=True) # Nombre de la persona de contacto
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Cliente('{self.nombre_empresa}')"

# Definición del modelo para Historial de Avance
class HistorialAvance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id'), nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    porcentaje_anterior = db.Column(db.Integer, nullable=False)
    porcentaje_nuevo = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"HistorialAvance(ObraID:{self.obra_id}, {self.porcentaje_anterior}% -> {self.porcentaje_nuevo}%)"

# Definición del modelo para Documentos
class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id'), nullable=False)
    tipo_documento = db.Column(db.String(100), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(500), nullable=False) # URL donde se almacena el documento (ej: S3, Google Drive)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Documento('{self.nombre_archivo}', ObraID:{self.obra_id})"

# Asegurarse de que las tablas se creen al inicio si no existen.
# Esto se hace dentro del contexto de la aplicación, una sola vez.
with app.app_context():
    db.create_all()

# Rutas de la aplicación
@app.route('/', endpoint='index') # <-- CAMBIO APLICADO AQUÍ
def index():
    return render_template('index.html', title='Inicio')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() # Revierte la transacción en caso de error
            if 'unique constraint' in str(e) or 'duplicate key' in str(e).lower():
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
    obras = Obra.query.all() # Obtener todas las obras para mostrar en el dashboard
    return render_template('dashboard.html', title='Dashboard', obras=obras)

@app.route('/add_obra', methods=['GET', 'POST'])
def add_obra():
    if request.method == 'POST':
        nombre_obra = request.form.get('nombre_obra')
        estado = request.form.get('estado')
        porcentaje_avance = request.form.get('porcentaje_avance')
        observaciones = request.form.get('observaciones')

        # Convertir porcentaje_avance a entero si no es None y el estado es 'En proceso'
        if estado == 'En proceso' and porcentaje_avance:
            try:
                porcentaje_avance = int(porcentaje_avance)
            except ValueError:
                flash('El porcentaje de avance debe ser un número entero.', 'danger')
                return render_template('add_obra.html', title='Añadir Obra')
        else:
            porcentaje_avance = None # Si no está en proceso, el porcentaje no aplica

        new_obra = Obra(
            nombre_obra=nombre_obra,
            estado=estado,
            porcentaje_avance=porcentaje_avance,
            observaciones=observaciones
        )
        db.session.add(new_obra)
        db.session.commit()
        flash('Obra añadida exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_obra.html', title='Añadir Obra')

@app.route('/ver_obras')
def ver_obras():
    obras = Obra.query.all()
    return render_template('ver_obras.html', title='Ver Obras', obras=obras)

@app.route('/ver_clientes')
def ver_clientes():
    clientes = Cliente.query.all()
    return render_template('ver_clientes.html', title='Ver Clientes', clientes=clientes)

@app.route('/ver_documentos/<int:obra_id>')
def ver_documentos(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    documentos = Documento.query.filter_by(obra_id=obra_id).all()
    return render_template('ver_documentos.html', title=f'Documentos de {obra.nombre_obra}', obra=obra, documentos=documentos)

@app.route('/ver_historial_avance/<int:obra_id>')
def ver_historial_avance(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    historial = HistorialAvance.query.filter_by(obra_id=obra_id).order_by(HistorialAvance.fecha_actualizacion.desc()).all()
    return render_template('ver_historial_avance.html', title=f'Historial de Avance de {obra.nombre_obra}', obra=obra, historial=historial)


if __name__ == '__main__':
    app.run(debug=True)