from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO
from flask_login import LoginManager, login_user, login_required, current_user,logout_user
from random import randint
from models.models import User
from utils import hash_password, verify_password,generate_random_color
import db_session

app = Flask(__name__)
app.config["SECRET_KEY"] = "example"
login_manager = LoginManager()
login_manager.login_view = "login"
socket = SocketIO(app)
login_manager.init_app(app)
players = {}
users = {}
count_players = 0


def get_db():
    db = db_session.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@login_manager.user_loader
def load_user(user_id):
    db = next(get_db())
    return db.query(User).filter(User.id == user_id).first()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html",user = current_user)
    if request.method == "POST":
        db = next(get_db())
        data = request.form
        if data["password1"] == data["password2"]:
            user = User()
            user.username = data["username"]
            user.hashed_password = hash_password(data["password1"])
            user.color = generate_random_color()
            db.add(user)
            db.commit()
            return redirect("/")
        return render_template("register.html",user = current_user, error="Пароли не совпадают!")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html",user = current_user)
    if request.method == "POST":
        db = next(get_db())
        data = request.form
        if db.query(User).filter(User.username == data["username"]).first():
            user = db.query(User).filter(User.username == data["username"]).first()
            if verify_password(data["password1"], user.hashed_password):
                login_user(user)
                return redirect("/")
            return render_template("login.html", user = current_user,error="Неверный пароль!")
        return render_template("login.html", user = current_user,error="Пользователя не существует")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "GET":
        db = next(get_db())
        user = db.query(User).filter(User.id == current_user.id).first()
        return render_template("profile.html", user = user)
    if request.method == "POST":
        db = next(get_db())
        data = request.form
        user = db.query(User).filter(User.id == current_user.id).first()
        user.username = data["username"]
        db.add(user)
        db.commit()
        print(data["color"])
        return render_template("profile.html", user = user)


@socket.on("connect")
def on_connect():
    global players, count_players
    username = f"Гость{count_players}"
    print(current_user)
    if current_user.is_anonymous == False:
        username = current_user.username
    players[request.sid] = {
        "username": username,
        "x": randint(0, 750),
        "y": randint(0, 750),
    }
    count_players += 1
    socket.emit("ur_sid", {"id": request.sid}, to=request.sid)
    socket.emit("update_all", players)


@socket.on("disconnect")
def on_disconnect():
    global players, count_players
    players.pop(request.sid, None)
    count_players -= 1
    socket.emit("update_all", players)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@socket.on("move")
def on_move(data):
    if request.sid in players:
        players[request.sid]["x"] = data["x"]
        players[request.sid]["y"] = data["y"]
        socket.emit("update_all", players)


socket.run(app, debug=True)
