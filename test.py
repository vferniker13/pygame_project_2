from flask import Flask, render_template
from flask_socketio import SocketIO, send


app = Flask(__name__)
app.config['SECRET_KEY'] = 'example'
socket = SocketIO(app)


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@socket.on('message')
def handle_message(data):
    message = data['message']
    author = data['author']
    print(author)
    send(message, broadcast=True)


socket.run(app, debug=True)
