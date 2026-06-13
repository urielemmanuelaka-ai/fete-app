import os
import secrets
import string

from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-moi-plus-tard'

socketio = SocketIO(app, cors_allowed_origins="*")


def generate_room_code(length=6):
    """Génère un code de salon aléatoire, ex: 'a1b2c3'."""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@app.route('/')
def home():
    """Page d'accueil : créer ou rejoindre un salon."""
    return render_template('home.html')


@app.route('/creer-salon', methods=['POST'])
def creer_salon():
    """Crée un nouveau salon avec un code unique et redirige vers celui-ci."""
    code = generate_room_code()
    return redirect(url_for('salon', code=code))


@app.route('/salon/<code>')
def salon(code):
    """Affiche la page du salon de fête correspondant au code."""
    return render_template('room.html', room_code=code)


@socketio.on('join')
def handle_join(data):
    """Place l'utilisateur dans la 'room' SocketIO correspondant à son salon."""
    room_code = data.get('room')
    join_room(room_code)
    print(f"Un utilisateur a rejoint le salon : {room_code}")


@socketio.on('trigger_effect')
def handle_effect(data):
    """
    Reçoit un effet déclenché par un utilisateur dans un salon donné
    et le renvoie UNIQUEMENT aux personnes de ce même salon.
    """
    room_code = data.get('room')
    effect = data.get('effect')
    print(f"Effet '{effect}' déclenché dans le salon {room_code}")
    emit('play_effect', {'effect': effect}, room=room_code)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
