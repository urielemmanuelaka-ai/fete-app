import os
import secrets
import string

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-moi-plus-tard'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fete.db'

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tokens = db.Column(db.Integer, default=0)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def generate_room_code(length=6):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("Merci de remplir tous les champs.")
            return redirect(url_for('inscription'))

        if User.query.filter_by(email=email).first():
            flash("Un compte existe deja avec cet email.")
            return redirect(url_for('inscription'))

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est deja pris.")
            return redirect(url_for('inscription'))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            tokens=0
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('inscription.html')


@app.route('/connexion', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))

        flash("Email ou mot de passe incorrect.")
        return redirect(url_for('login'))

    return render_template('connexion.html')


@app.route('/deconnexion')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/creer-salon', methods=['POST'])
@login_required
def creer_salon():
    code = generate_room_code()
    return redirect(url_for('salon', code=code))


@app.route('/salon/<code>')
@login_required
def salon(code):
    return render_template('room.html', room_code=code)


@socketio.on('join')
def handle_join(data):
    room_code = data.get('room')
    join_room(room_code)
    print(f"Un utilisateur a rejoint le salon : {room_code}")


@socketio.on('trigger_effect')
def handle_effect(data):
    room_code = data.get('room')
    effect = data.get('effect')
    print(f"Effet '{effect}' declenche dans le salon {room_code}")
    emit('play_effect', {'effect': effect}, room=room_code)


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)