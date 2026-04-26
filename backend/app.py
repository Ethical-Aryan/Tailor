import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app) 

basedir = os.path.abspath(os.path.dirname(__file__))

# Render provides DATABASE_URL. SQLAlchemy needs postgresql:// instead of postgres://
db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'database.db'))
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(basedir, '..', 'frontend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SHOP_DETAILS = {
    'whatsapp_number': '917045464243', # Replace with real number
    'shop_name': 'Raj Tailors'
}

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        image_url = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = '/uploads/' + filename
        
        # Fallback to text input if they still wanted to provide a URL manually (optional)
        if not image_url:
            image_url = request.form.get('image_url')

        new_product = Product(name=name, description=description, price=float(price), image_url=image_url)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('admin'))
    
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    output = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'image_url': product.image_url
        }
        output.append(product_data)
    return jsonify({
        'products': output,
        'shop_details': SHOP_DETAILS
    })

@app.route("/health")
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
