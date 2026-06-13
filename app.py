from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-moi-plus-tard'

# cors_allowed_origins="*" permet aux clients de se connecter depuis n'importe où
# (utile pour les tests, à restreindre plus tard en production)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    """Page principale : le salon de fête."""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print("Un nouvel utilisateur s'est connecté :", request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print("Un utilisateur s'est déconnecté :", request.sid)


@socketio.on('trigger_effect')
def handle_effect(data):
    """
    Reçoit un effet déclenché par un utilisateur (ex: {"effect": "confetti"})
    et le renvoie à TOUT LE MONDE connecté (broadcast=True), y compris
    celui qui a cliqué.
    """
    print("Effet déclenché :", data)
    emit('play_effect', data, broadcast=True)


if __name__ == '__main__':
    # debug=True redémarre le serveur automatiquement quand tu modifies le code
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
