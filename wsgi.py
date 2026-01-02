from main import create_app
from main import socket, login_manager

app = create_app()
socket.init_app(app)
login_manager.init_app(app)