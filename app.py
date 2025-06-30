import os # ¡NUEVO! Importa el módulo os para variables de entorno
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# from werkzeug.security import generate_password_hash, check_password_hash # Descomentar cuando implementemos seguridad real

# Inicializa la aplicación Flask
app = Flask(__name__)

# --- Configuración de la Base de Datos PostgreSQL ---
# ¡ACTUALIZADO! Lee DATABASE_URL de las variables de entorno, o usa localhost como fallback.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:Amda5296@localhost:5432/total_energy_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desactiva el seguimiento de modificaciones para ahorrar recursos
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_secreta_super_segura_aqui') # Lee SECRET_KEY de las variables de entorno

# Inicializa SQLAlchemy con la aplicación Flask
db = SQLAlchemy(app)

# --- Define los Modelos de Base de Datos ---

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default='cliente')
    fecha_registro = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(255), unique=True, nullable=False)
    cuit = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.String(255))
    
    contacto_principal_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    
    fecha_registro = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    contacto_principal = db.relationship('Usuario', backref='clientes_contacto', foreign_keys=[contacto_principal_id])
    obras = db.relationship('Obra', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre_empresa}>'

class Obra(db.Model):
    __tablename__ = 'obras'
    id = db.Column(db.Integer, primary_key=True)
    nombre_obra = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(50), nullable=False, default='en_ejecucion')
    porcentaje_avance = db.Column(db.Integer, nullable=False, default=0)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin_estimada = db.Column(db.Date)
    fecha_fin_real = db.Column(db.Date)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)

    documentos = db.relationship('DocumentoObra', backref='obra', lazy=True)
    historial_avance = db.relationship('HistorialAvance', backref='obra', lazy=True)

    def __repr__(self):
        return f'<Obra {self.nombre_obra}>'

class DocumentoObra(db.Model):
    __tablename__ = 'documentos_obra'
    id = db.Column(db.Integer, primary_key=True)
    
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id', ondelete='CASCADE'), nullable=False)
    
    tipo_documento = db.Column(db.String(100), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(500), nullable=False)
    fecha_subida = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Documento {self.nombre_archivo} ({self.tipo_documento})>'

class HistorialAvance(db.Model):
    __tablename__ = 'historial_avance'
    id = db.Column(db.Integer, primary_key=True)
    
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id', ondelete='CASCADE'), nullable=False)
    
    fecha_actualizacion = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    porcentaje_anterior = db.Column(db.Integer)
    porcentaje_nuevo = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text)

    def __repr__(self):
        return f'<Avance Obra {self.obra_id} - {self.porcentaje_nuevo}%>'


# --- Rutas de la Aplicación Flask ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agregar_usuario/<nombre>/<email>/<password>')
def agregar_usuario(nombre, email, password):
    try:
        nuevo_usuario = Usuario(nombre=nombre, email=email, password_hash=password, rol='cliente')
        db.session.add(nuevo_usuario)
        db.session.commit()
        return f'Usuario {nombre} con email {email} y rol cliente agregado con éxito!'
    except Exception as e:
        db.session.rollback()
        if "unique constraint" in str(e).lower():
            return f'Error: Ya existe un usuario con ese nombre o email. Detalle: {e}'
        return f'Error al agregar usuario: {e}'

@app.route('/ver_usuarios')
def ver_usuarios():
    usuarios = Usuario.query.all()
    return render_template('ver_usuarios.html', usuarios=usuarios)


# --- Rutas para la gestión de Clientes ---

@app.route('/agregar_cliente/<nombre_empresa>/<cuit>')
def agregar_cliente(nombre_empresa, cuit):
    try:
        nuevo_cliente = Cliente(nombre_empresa=nombre_empresa, cuit=cuit)
        db.session.add(nuevo_cliente)
        db.session.commit()
        return f'Cliente {nombre_empresa} con CUIT {cuit} agregado con éxito!'
    except Exception as e:
        db.session.rollback()
        if "unique constraint" in str(e).lower():
            return f'Error: Ya existe un cliente con ese nombre o CUIT. Detalle: {e}'
        return f'Error al agregar cliente: {e}'

@app.route('/ver_clientes')
def ver_clientes():
    clientes = Cliente.query.all()
    return render_template('ver_clientes.html', clientes=clientes)

# --- Rutas para la gestión de Obras ---

@app.route('/agregar_obra/<nombre_obra>/<int:cliente_id>/<fecha_inicio>')
def agregar_obra(nombre_obra, cliente_id, fecha_inicio):
    try:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()

        cliente_existente = Cliente.query.get(cliente_id)
        if not cliente_existente:
            return f'Error: No existe un cliente con ID {cliente_id}. Agrega el cliente primero.'

        nueva_obra = Obra(
            nombre_obra=nombre_obra,
            descripcion="Descripción de prueba",
            cliente_id=cliente_id,
            fecha_inicio=fecha_inicio_obj,
            estado='en_ejecucion',
            porcentaje_avance=0
        )
        db.session.add(nueva_obra)
        db.session.commit()
        return f'Obra "{nombre_obra}" agregada con éxito para el cliente {cliente_existente.nombre_empresa}!'
    except ValueError:
        db.session.rollback()
        return 'Error: Formato de fecha_inicio incorrecto. Usa AAAA-MM-DD.'
    except Exception as e:
        db.session.rollback()
        return f'Error al agregar obra: {e}'

@app.route('/ver_obras')
def ver_obras():
    obras = Obra.query.all()
    return render_template('ver_obras.html', obras=obras)

# --- Rutas para la gestión de Documentos de Obra ---

@app.route('/agregar_documento/<int:obra_id>/<tipo_documento>/<nombre_archivo>/<path:url_archivo>')
def agregar_documento(obra_id, tipo_documento, nombre_archivo, url_archivo):
    try:
        obra_existente = Obra.query.get(obra_id)
        if not obra_existente:
            return f'Error: No existe una obra con ID {obra_id}. Agrega la obra primero.'

        nuevo_documento = DocumentoObra(
            obra_id=obra_id,
            tipo_documento=tipo_documento,
            nombre_archivo=nombre_archivo,
            url_archivo=url_archivo
        )
        db.session.add(nuevo_documento)
        db.session.commit()
        return f'Documento "{nombre_archivo}" agregado con éxito para la obra "{obra_existente.nombre_obra}"!'
    except Exception as e:
        db.session.rollback()
        return f'Error al agregar documento: {e}'

@app.route('/ver_documentos/<int:obra_id>')
def ver_documentos(obra_id):
    obra = Obra.query.get(obra_id)
    if not obra:
        return f'No existe una obra con ID {obra_id}.'
    
    documentos = DocumentoObra.query.filter_by(obra_id=obra_id).all()
    return render_template('ver_documentos.html', obra=obra, documentos=documentos)

# --- Rutas para la gestión del Historial de Avance ---

@app.route('/registrar_avance/<int:obra_id>/<int:porcentaje_nuevo>/<comentarios>')
def registrar_avance(obra_id, porcentaje_nuevo, comentarios):
    try:
        obra_existente = Obra.query.get(obra_id)
        if not obra_existente:
            return f'Error: No existe una obra con ID {obra_id}.'

        porcentaje_anterior = obra_existente.porcentaje_avance

        nuevo_avance = HistorialAvance(
            obra_id=obra_id,
            porcentaje_anterior=porcentaje_anterior,
            porcentaje_nuevo=porcentaje_nuevo,
            comentarios=comentarios
        )
        db.session.add(nuevo_avance)
        obra_existente.porcentaje_avance = porcentaje_nuevo
        
        db.session.commit()
        return f'Avance del {porcentaje_nuevo}% registrado para la obra "{obra_existente.nombre_obra}". Avance anterior: {porcentaje_anterior}%'
    except Exception as e:
        db.session.rollback()
        return f'Error al registrar avance: {e}'

@app.route('/ver_historial_avance/<int:obra_id>')
def ver_historial_avance(obra_id):
    obra = Obra.query.get(obra_id)
    if not obra:
        return f'No existe una obra con ID {obra_id}.'

    historial = HistorialAvance.query.filter_by(obra_id=obra_id).order_by(HistorialAvance.fecha_actualizacion.desc()).all()
    return render_template('ver_historial_avance.html', obra=obra, historial=historial)


# --- Rutas de Autenticación Básica ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = Usuario.query.filter_by(email=email).first()

        # ¡OJO! Esto NO es seguro para producción. Las contraseñas deben ser hasheadas.
        if user and user.password_hash == password:
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            session['user_rol'] = user.rol
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenciales incorrectas.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_name = session['user_name']
        user_rol = session['user_rol']
        return render_template('dashboard.html', user_name=user_name, user_rol=user_rol)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_rol', None)
    return redirect(url_for('index'))


# Este bloque solo se ejecuta si corres el archivo directamente
if __name__ == '__main__':
    print("Creando tablas de la base de datos si no existen...")
    with app.app_context():
        try:
            db.create_all()
            print("Tablas creadas/verificadas.")
        except Exception as e:
            print(f"Error al intentar crear/verificar tablas: {e}")
            print("Asegúrate de que la base de datos 'total_energy_db' exista y que el usuario 'postgres' tenga permisos.")

    print("Intentando iniciar el servidor Flask...")
    try:
        # Flask usa el puerto 5000 por defecto para debug
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"ERROR al iniciar Flask: {e}")