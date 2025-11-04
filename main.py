from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO
from random import randint


app = Flask(__name__)
app.config['SECRET_KEY'] = 'example'
socket = SocketIO(app)
players = {}
users = {}
count_players = 0


@app.route("/", methods=['GET'])
def index():
    username = session.get('username')
    return render_template("index.html", username=username)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        data = request.form
        if data['password1'] == data['password2']:
            users[data['username']] = {'id': randint(1000000, 999999999),'password': data['password1']}
            return redirect('/')
        return render_template("register.html", error='Пароли не совпадают!')


@socket.on('connect')
def on_connect():
    global players, count_players
    players[request.sid] = {"username": f"Гость{count_players}", "x": randint(0, 750), "y": randint(0, 750)}
    count_players += 1
    socket.emit('ur_sid', {'id': request.sid}, to=request.sid)
    socket.emit('update_all', players)


@socket.on('disconnect')
def on_disconnect():
    global players, count_players
    players.pop(request.sid, None)
    count_players -= 1
    socket.emit('update_all', players)


@socket.on('move')
def on_move(data):
    if request.sid in players:
        players[request.sid]["x"] = data["x"]
        players[request.sid]["y"] = data["y"]
        socket.emit('update_all', players)


socket.run(app, debug=True)

