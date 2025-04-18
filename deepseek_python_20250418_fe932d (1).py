from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import pyotp
import os
from datetime import datetime
from functools import wraps
from allegro_api.auth import AllegroAPI
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Konfiguracja
ALLOWED_IPS = ['127.0.0.1', '192.168.1.1']  # Zmień!
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)
TOTP_SECRET = pyotp.random_base32()

# Modele
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    encrypted_password = db.Column(db.String(255), nullable=False)
    offer_id = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class MessageTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_template = db.Column(db.Text, default="Witaj, konto: {{email}}:{{password}}")
    delay_template = db.Column(db.Text, default="Opóźnienie 24h!")

# Helpery
def get_oldest_account(offer_id):
    return Account.query.filter_by(offer_id=offer_id, verified=True).order_by(Account.created_at).first()

# Security
@app.before_request
def security_checks():
    if request.remote_addr not in ALLOWED_IPS:
        abort(403)
    if '2fa_verified' not in session and request.endpoint not in ['verify_2fa', 'static']:
        return redirect(url_for('verify_2fa'))

# Routes
@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if request.method == 'POST':
        if pyotp.TOTP(TOTP_SECRET).verify(request.form['code']):
            session['2fa_verified'] = True
            return redirect(url_for('orders'))
    return render_template('2fa.html')

@app.route('/orders')
def orders():
    allegro = AllegroAPI(os.getenv('ALLEGRO_CLIENT_ID'), os.getenv('ALLEGRO_CLIENT_SECRET'))
    allegro.authenticate()
    orders = allegro.get_orders()
    return render_template('orders.html', orders=orders)

@app.route('/send_account/<offer_id>/<order_id>')
def send_account(offer_id, order_id):
    account = get_oldest_account(offer_id)
    if account:
        allegro.send_message(order_id, render_template('message.txt', account=account))
        db.session.delete(account)
        db.session.commit()
    else:
        allegro.send_message(order_id, MessageTemplate.query.first().delay_template)
    return redirect(url_for('orders'))

# ... (reszta endpointów z poprzednich wiadomości)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not MessageTemplate.query.first():
            db.session.add(MessageTemplate())
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')