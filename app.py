from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

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

# Crear todas las tablas de la base de datos
with app.app_context():
    db.create_all()

# Ruta de Bienvenida
@app.route('/')
def bienvenida():
    return render_template('bienvenida.html')

# Rutas para Clientes
@app.route('/clientes', methods=['GET'])
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
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente.')
    return redirect(url_for('listar_clientes'))

# Rutas para Facturas
@app.route('/facturas', methods=['GET'])
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
def eliminar_factura(id):
    factura = Factura.query.get_or_404(id)
    db.session.delete(factura)
    db.session.commit()
    flash('Factura eliminada correctamente.')
    return redirect(url_for('listar_facturas'))

# Ruta para generar reporte de facturas en PDF
@app.route('/api/invoices/report', methods=['GET'])
def generate_report():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Título
    p.drawString(100, 750, "Reporte de Facturas")
    
    # Obtener facturas de la base de datos
    facturas = Factura.query.all()
    
    # Generar las líneas para las facturas
    y = 730
    for factura in facturas:
        cliente = Cliente.query.get(factura.cliente_id)
        p.drawString(100, y, f"Factura #{factura.id} - Cliente: {cliente.nombre} - Fecha: {factura.fecha} - Monto: {factura.monto}")
        y -= 20  # Ajustar la posición vertical

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='reporte_facturas.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)