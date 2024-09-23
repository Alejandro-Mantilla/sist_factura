from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import timedelta
import re
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///facturas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

# Configuración de seguridad adicionales
app.config['SECRET_KEY'] = 'supersecretkey' 
app.config['SESSION_COOKIE_HTTPONLY'] = True # Protección contra ataques XSS
app.config['SESSION_COOKIE_SECURE'] = True # Cookies solo disponible vía HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Protege contra ataques CSRF
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7) 

db = SQLAlchemy(app)
# Inicio de Sesión
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Definir el modelo de Usuario
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# Definir el modelo de Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(10), nullable=False)

# Definir el modelo de Factura
class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('facturas', lazy=True))

# Crear todas las tablas de la base de datos
with app.app_context():
    db.create_all()

# Función para verificar la fortaleza de la contraseña
def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[\W]", password):
        return False, "Password must contain at least one special character"
    return True, ""

# Ruta de Inicio de Sesión
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Ruta para el registro de nuevo usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validación de la fortaleza de la contraseña
        valid, message = is_strong_password(password)
        if not valid:
            flash(message)
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        nuevo_usuario = Usuario(username=username, password=hashed_password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario registrado correctamente')
        return redirect(url_for('login'))
    return render_template('register.html')

# Ruta para el inicio de sesión

limiter = Limiter(get_remote_address, app=app)

@limiter.limit(' 5 per 10 minutes') # Limita a 5 intentos de inicio de sesión cada 10 minutos
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            flash('Inicio de sesión exitoso')
            return redirect(url_for('listar_clientes'))
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente')
    return redirect(url_for('login'))

# Ruta de Bienvenida
@app.route('/')
def bienvenida():
    return render_template('bienvenida.html')

# Rutas para Clientes
@app.route('/clientes', methods=['GET'])
@login_required
def listar_clientes():
    query = request.args.get('q')
    if query:
        clientes = Cliente.query.filter(
            (Cliente.nombre.like(f'%{query}%')) |
            (Cliente.email.like(f'%{query}%'))
        ).all()
    else:
        clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        
        # Validaciones
        if len(nombre) < 2:
            flash('El nombre debe tener al menos 2 caracteres.')
            return redirect(url_for('nuevo_cliente'))
        if not telefono.isdigit() or len(telefono) != 10:
            flash('El teléfono debe tener 10 dígitos.')
            return redirect(url_for('nuevo_cliente'))
        
        nuevo_cliente = Cliente(nombre=nombre, email=email, telefono=telefono)
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente agregado correctamente.')
        return redirect(url_for('listar_clientes'))
    
    return render_template('nuevo_cliente.html')

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        
        # Validaciones
        if len(nombre) < 2:
            flash('El nombre debe tener al menos 2 caracteres.')
            return redirect(url_for('editar_cliente', id=id))
        if not telefono.isdigit() or len(telefono) != 10:
            flash('El teléfono debe tener 10 dígitos.')
            return redirect(url_for('editar_cliente', id=id))
        
        cliente.nombre = nombre
        cliente.email = email
        cliente.telefono = telefono
        db.session.commit()
        flash('Cliente actualizado correctamente.')
        return redirect(url_for('listar_clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente.')
    return redirect(url_for('listar_clientes'))

# Rutas para Facturas
@app.route('/facturas', methods=['GET'])
@login_required
def listar_facturas():
    fecha = request.args.get('fecha')
    cliente_id = request.args.get('cliente_id')
    monto_minimo = request.args.get('monto_minimo')
    monto_maximo = request.args.get('monto_maximo')
    
    query = Factura.query
    
    if fecha:
        query = query.filter(Factura.fecha == fecha)
    if cliente_id:
        query = query.filter(Factura.cliente_id == cliente_id)
    if monto_minimo:
        query = query.filter(Factura.monto >= float(monto_minimo))
    if monto_maximo:
        query = query.filter(Factura.monto <= float(monto_maximo))
        
    facturas = query.all()
    clientes = Cliente.query.all()  # Filtro para buscar por cliente
    return render_template('facturas.html', facturas=facturas, clientes=clientes)

@app.route('/facturas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha = request.form['fecha']
        monto = request.form['monto']
        
        # Validaciones
        if not monto or not monto.replace('.', '', 1).isdigit():
            flash('El monto debe ser un número válido.')
            return redirect(url_for('nueva_factura'))
        
        nueva_factura = Factura(cliente_id=cliente_id, fecha=fecha, monto=float(monto))
        db.session.add(nueva_factura)
        db.session.commit()
        flash('Factura agregada correctamente.')
        return redirect(url_for('listar_facturas'))
    
    clientes = Cliente.query.all()
    return render_template('nueva_factura.html', clientes=clientes)

@app.route('/facturas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_factura(id):
    factura = Factura.query.get_or_404(id)
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha = request.form['fecha']
        monto = request.form['monto']
        
        # Validaciones
        if not monto or not monto.replace('.', '', 1).isdigit():
            flash('El monto debe ser un número válido.')
            return redirect(url_for('editar_factura', id=id))
        
        factura.cliente_id = cliente_id
        factura.fecha = fecha
        factura.monto = float(monto)
        db.session.commit()
        flash('Factura actualizada correctamente.')
        return redirect(url_for('listar_facturas'))
    
    clientes = Cliente.query.all()
    return render_template('editar_factura.html', factura=factura, clientes=clientes)

@app.route('/facturas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_factura(id):
    factura = Factura.query.get_or_404(id)
    db.session.delete(factura)
    db.session.commit()
    flash('Factura eliminada correctamente.')
    return redirect(url_for('listar_facturas'))

# Generación de PDF
@app.route('/facturas/generar_pdf/<int:id>', methods=['GET'])
@login_required
def generar_pdf(id):
    factura = Factura.query.get_or_404(id)
    cliente = Cliente.query.get(factura.cliente_id)

    # Generar PDF en memoria
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.drawString(100, 750, f"Factura ID: {factura.id}")
    c.drawString(100, 730, f"Cliente: {cliente.nombre}")
    c.drawString(100, 710, f"Email: {cliente.email}")
    c.drawString(100, 690, f"Teléfono: {cliente.telefono}")
    c.drawString(100, 670, f"Fecha: {factura.fecha}")
    c.drawString(100, 650, f"Monto: ${factura.monto:.2f}")

    c.save()

    # Configurar el archivo para ser descargado
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"factura_{factura.id}.pdf", mimetype='application/pdf')

# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)