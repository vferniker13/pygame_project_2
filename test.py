from flask import Flask, render_template, request
from flask_socketio import SocketIO, send


app = Flask(__name__)
app.config['SECRET_KEY'] = 'example'
socket = SocketIO(app)
players = {}
count_players = 0


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@socket.on('connect')
def on_connect():
    global players, count_players
    players[request.sid] = {"username": f"Гость{count_players}", "x": 100, "y": 100}
    count_players += 1
    socket.emit('players')


@socket.on('disconnect')
def on_disconnect():
    global players, count_players
    players.pop(request.sid, None)
    count_players -= 1


@socket.on('move')
def on_move(data):
    if request.sid in players:
        players[request.sid]["x"] = data["x"]
        players[request.sid]["y"] = data["y"]
        socket.emit('update_you', {"x": data["x"], "y": data["y"]}, to=request.sid)
    socket.emit('update_all', players)


socket.run(app, debug=True)

