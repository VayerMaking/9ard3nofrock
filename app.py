from flask import Flask
from flask import render_template, request, flash, redirect, url_for, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
import time
import os
from datetime import datetime
import hashlib
import enum

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', None)
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://') or 'sqlite:///todo.db'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    address = db.Column(db.String(150))
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    order_status = db.Column(db.String(100)) #order_status will possibly be edited manually through the db

    def verify(self, thing_to_verify):
        return self.thing_to_verify == hash_password(thing_to_verify)

class Bucket(db.Model):
    __tablename__ = 'bucket'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref=db.backref("user", uselist=False))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)

class Sizes(enum.Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class Colors(enum.Enum):
    white = "White"
    black = "Black"
    red = "Red"
    blue = "Blue"

# class Designs(enum.Enum):
#     original = "Original"
#     inverted = "Inverted"

class Band(db.Model):
    __tablename__ = 'band'
    id = db.Column(db.Integer, primary_key = True)
    band_name = db.Column(db.String(100))
    band_desc = db.Column(db.String(1000))
    band_pic = db.Column(db.String(64))
    band_email = db.Column(db.String(100))
    band_facebook = db.Column(db.String(100))
    band_instagram = db.Column(db.String(100))
    band_bandcamp = db.Column(db.String(100))
    band_spotify = db.Column(db.String(100))
    band_youtube = db.Column(db.String(100))

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key = True)
    size = db.Column(db.Enum(Sizes), nullable=False)
    color = db.Column(db.Enum(Colors), nullable=False)
    band_id = db.Column(db.Integer, db.ForeignKey('band.id'))
    band = db.relationship("Band", backref=db.backref("band", uselist=False))
    #design = db.Column(db.Enum(Designs), nullable=False)

def hash_password(thing_to_hash):
    return hashlib.sha256(thing_to_hash.encode('utf-8')).hexdigest()

def email_link(user_id):
    links = User.query.all()
    return links[user_id].email
    # when we get the email we should email a paypal link to it
    # verification of the payment probably will be done manually by a human

@app.route('/', methods=['GET'])
def index():
    if 'username' in session:
        username = session['username']
    else:
        username = "Guest"
    products = Product.query.all()
    print("All products: ", products)
    return render_template('index.html', username=username, products=products)

@app.route('/paypal', methods=['GET'])
def paypal():
    return render_template('paypal.html')

@app.route('/products', methods=['GET', 'POST'])
def products():
    products = Product.query.filter_by(id = request.args.get('band_id')).all()
    return render_template('products.html', products=products)

@app.route('/product', methods=['GET', 'POST'])
def product():
    product = Product.query.filter_by(id = request.args.get('product_id')).all()
    return render_template('product.html', product=product)

@app.route('/band', methods=['GET', 'POST'])
def band():
    band = Band.query.filter_by(id = request.args.get('band_id')).first()
    return render_template('band_page.html', band=band)

@app.route('/add_to_bucket', methods=['GET', 'POST'])
def add_to_bucket():
    req = request.get_json()

    # print("req: ", req)

    res = make_response(jsonify({"message": "OK"}), 200)

    # print("color: ", req['color'])
    # print("size: ", req['size'])
    # print("design: ", req['design'])
    #product = Product.query.filter_by(color=req['color'], size=req['size']).first()
    product = Product.query.filter_by(id=req['product_id']).first()
    # print(product)
    user_id=request.form.get('user_id')
    # print(product.id)
    bucket = Bucket(user_id=session['user_id'], product_id=product.id)

    # print(bucket.id)
    # print(bucket.user_id)
    # print(bucket.product_id)
    db.session.add(bucket)
    db.session.commit()
    return res
    return "success"

@app.route('/bucket', methods=['GET'])
def get_bucket():
    buckets = Bucket.query.filter_by(user_id=session['user_id']).all()
    try:
        user = User.query.filter_by(id=buckets[0].user_id).first()
    except IndexError:
        return render_template('empty_bucket.html')
    product_ids = []
    for bucket in buckets:
        product_ids.append(bucket.product_id)
    products = []
    for product_id in product_ids:
        product = Product.query.filter_by(id=product_id).first()
        products.append(product)

    return render_template('bucket.html', bucket=bucket, user=user, products=products)

@app.route('/preorder', methods=['GET', 'POST'])
def preorder():
    if request.method == "POST":
        data = request.form
        #print(data['name'], data['email'], data['address'])
        user = User.query.filter_by(username=session['username']).first()
        #user = User(name=data['name'], email=data['email'], address=data['address'])
        #should be an update not 2 separate instances of the class
        user.name = data['name']
        user.email = data['email']
        user.address = data['address']
        db.session.add(user)
        db.session.commit()

        return render_template('succesfull_preorder.html', name=user.name)
    elif request.method == "GET":

        return render_template("preorder.html")
    #return render_template('preorder.html')
@app.route('/email', methods=['GET'])
def email():
    return email_link(5)

@app.route('/status', methods=['GET'])
def status():
    user = User.query.filter_by(username=session['username']).first()
    print("order_status", user.order_status)
    return render_template('preorder_status.html', username=session['username'], order_status=user.order_status)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: throw a warning for usernames that are already used, bacause it would f*ck up preorder
    if request.method == "POST":
        data = request.form
        if not User.query.filter_by(username=data['username']).first():
            user = User(username=data['username'], password=hash_password(data['password']))
            db.session.add(user)
            db.session.commit()
        else:
            return "username not avaible"

        return render_template('login.html')
    elif request.method == "GET":

        return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        data = request.form
        user = User.query.filter_by(username=data['username'], password=hash_password(data['password'])).first()
        if not user:
            return render_template("login.html", message="invalid credentials")

        session['username'] = data['username']
        session['user_id'] = user.id
        session['logged_in'] = True

        return redirect(('/'))

    elif request.method == "GET":
        return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    session['logged_in'] = False
    return redirect('/')

@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    req = request.get_json()
    print(req)
    buckets = Bucket.query.filter_by(user_id=session['user_id'], product_id=req['product_id']).delete()
    db.session.commit()
    print(buckets)
    res = make_response(jsonify({"message": "OK"}), 200)
    return res
    #return redirect('/')

db.create_all()
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
