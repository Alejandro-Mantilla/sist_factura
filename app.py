from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///facturas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

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

with app.app_context():
    db.create_all()
    
# Ruta de Bienvenida
@app.route('/')
def bienvenida():
    return render_template('bienvenida.html')

# Rutas para Clientes
@app.route('/clientes')
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
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
        return redirect(url_for('listar_clientes'))
    return render_template('nuevo_cliente.html')

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('listar_clientes'))
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/clientes/eliminar/<int:id>')
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for('listar_clientes'))

# Filtro --> Buscar Cliente
@app.route('/clientes/buscar', methods=['GET'])
def buscar_clientes():
    query = request.args.het('q')
    if query:
        clientes = Cliente.query.filter(
            (Cliente.nombre.like(f'%{query}%')) |
            (Cliente.email.like(f'%{query}%'))
        ).all()
    else:
        clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

# Rutas para Facturas
@app.route('/facturas')
def listar_facturas():
    facturas = Factura.query.all()
    return render_template('facturas.html', facturas=facturas)

@app.route('/facturas/nueva', methods=['GET', 'POST'])
def nueva_factura():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha = request.form['fecha']
        monto = request.form['monto']
        
        # Validaciones
        if not monto.replace('.', '', 1).isdigit():
            flash('El monto debe ser un número válido.')
            return redirect(url_for('nueva_factura'))
        
        nueva_factura = Factura(cliente_id=cliente_id, fecha=fecha, monto=float(monto))
        db.session.add(nueva_factura)
        db.session.commit()
        return redirect(url_for('listar_facturas'))
    clientes = Cliente.query.all()
    return render_template('nueva_factura.html', clientes=clientes)

@app.route('/facturas/editar/<int:id>', methods=['GET', 'POST'])
def editar_factura(id):
    factura = Factura.query.get_or_404(id)
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha = request.form['fecha']
        monto = request.form['monto']
        
        # Validaciones
        if not monto.replace('.', '', 1).isdigit():
            flash('El monto debe ser un número válido.')
            return redirect(url_for('editar_factura', id=id))
        
        factura.cliente_id = cliente_id
        factura.fecha = fecha
        factura.monto = float(monto)
        db.session.commit()
        return redirect(url_for('listar_facturas'))
    clientes = Cliente.query.all()
    return render_template('editar_factura.html', factura=factura, clientes=clientes)

@app.route('/facturas/eliminar/<int:id>')
def eliminar_factura(id):
    factura = Factura.query.get_or_404(id)
    db.session.delete(factura)
    db.session.commit()
    return redirect(url_for('listar_facturas'))

if __name__ == '__main__':
    app.run(debug=True)