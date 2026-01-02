from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
import math
import threading
import time
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    current_user,
    logout_user,
)
from random import randint
from models.models import User
from utils import (
    hash_password,
    verify_password,
    generate_random_color,
    generate_walls,
    is_obstacle_in_the_way,
    is_wall_on_the_line,
)
import db_session
import os

walls = {}
final = None


def create_app():
    global walls
    app = Flask(__name__)
    walls = generate_walls(10)
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = "example"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    return app


login_manager = LoginManager()
login_manager.login_view = "login"
socket = SocketIO()
players = {"hunter": None}
MAX_HUNTER = 1
info = {"total_hunters": 0, "max_hunters": MAX_HUNTER, "total_survivors": 0}
round_in_proccess = False


def get_db():
    db = db_session.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_to_game():
    global final, round_in_proccess
    socket.emit("start_wait", {"end_time": time.time() + 10})
    time.sleep(10)
    if players["hunter"]:
        final = time.time() + 10  # 180
        round_in_proccess = True
        socket.emit("start_game_timer", {"end_time": final})
        if players["hunter"] is None:
            stop_timer()


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
        return render_template("register.html", user=current_user)
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
        return render_template(
            "register.html", user=current_user, error="Пароли не совпадают!"
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=current_user)
    if request.method == "POST":
        db = next(get_db())
        data = request.form
        if db.query(User).filter(User.username == data["username"]).first():
            user = (
                db.query(User)
                .filter(User.username == data["username"])
                .first()
            )
            if verify_password(data["password1"], user.hashed_password):
                login_user(user)
                return redirect("/")
            return render_template(
                "login.html", user=current_user, error="Неверный пароль!"
            )
        return render_template(
            "login.html", user=current_user, error="Пользователя не существует"
        )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "GET":
        db = next(get_db())
        user = db.query(User).filter(User.id == current_user.id).first()
        return render_template("profile.html", user=user)
    if request.method == "POST":
        db = next(get_db())
        data = request.form
        user = db.query(User).filter(User.id == current_user.id).first()
        user.username = data["username"]
        user.color = data["color"]
        db.add(user)
        db.commit()
        return render_template("profile.html", user=user)


@app.route("/select/hunter/<sid>")
def become_hunter(sid: str):
    global players, info, round_in_proccess
    if not round_in_proccess and info["total_hunters"] < info["max_hunters"]:
        if not current_user.is_anonymous:
            players[sid]["role"] = "hunter"
            socket.emit("update_all", players)
            info["total_hunters"] += 1
            info["total_survivors"] -= 1
            players["hunter"] = sid
            socket.emit("update_info", info)
            if info["total_survivors"] <= 0:
                return {"status": 406}
            thread = threading.Thread(target=wait_to_game)
            thread.start()
            return {"status": 200}
        else:
            return {"status": 401}
    return {"status": 403}


@app.route("/select/survivor/<sid>")
def become_survivor(sid: str):
    global players, info, round_in_proccess
    if (
        not round_in_proccess
        and players[sid]["role"] == "hunter"
        and info["total_hunters"] > 0
    ):
        players["hunter"] = None
        info["total_hunters"] -= 1
    if players[sid]["role"] != "survivor":
        players[sid]["role"] = "survivor"
        info["total_survivors"] += 1
        socket.emit("update_all", players)
        socket.emit("update_info", info)
        return {"status": 200}
    return {"status": 403}


@socket.on("connect")
def on_connect():
    global players, info, walls, round_in_proccess
    username = f"Гость{info['total_survivors'] + info['total_hunters']}"
    if not current_user.is_anonymous:
        username = current_user.username
    players[request.sid] = {
        "username": username,
        "x": randint(0, 750),
        "y": randint(0, 750),
        "color": generate_random_color(),
        "role": "survivor",
        "is_alive": True if not round_in_proccess else False,
    }
    info["total_survivors"] += 1
    if not current_user.is_anonymous:
        players[request.sid]["color"] = current_user.color
    socket.emit("ur_sid", {"id": request.sid}, to=request.sid)
    socket.emit("update_all", players)
    socket.emit("update_walls", walls)
    socket.emit("update_info", info)


@socket.on("kill")
def kill_player(data: dict):
    global players, info, round_in_proccess
    if (
        round_in_proccess is True
        and players[data["target_id"]] != players["hunter"]
    ):
        players[data["target_id"]]["is_alive"] = False
        info["total_survivors"] -= 1
        hunter = players["hunter"]
        username = players[hunter]["username"]
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        user.kills += 1
        db.add(user)
        db.commit()
        socket.emit("kill_signal", data)
        socket.emit("update_info", info)
    stop_timer()
    socket.emit("update_all", players)


@socket.on("disconnect")
def on_disconnect():
    global players, info
    if players[request.sid]["role"] == "hunter":
        info["total_hunters"] -= 1
    else:
        info["total_survivors"] -= 1
    players[request.sid]["role"] = "survivor"
    players.pop(request.sid, None)
    socket.emit("update_all", players)
    socket.emit("update_info", info)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@socket.on("move")
def on_move(data: dict):
    global walls
    if request.sid in players:
        if (
            not is_obstacle_in_the_way(walls, data["x"], data["y"])
            and data["x"] + 10 < 800
            and data["x"] - 10 > 0
            and data["y"] + 10 < 800
            and data["y"] - 10 > 0
        ):
            players[request.sid]["x"] = data["x"]
            players[request.sid]["y"] = data["y"]
        socket.emit("update_all", players)


@socket.on("check_shot")
def on_shot(data: dict):
    global players, round_in_proccess
    for wall in walls:
        data_end = [data["shot_x"], data["shot_y"]]
        hunter = [
            players[players["hunter"]]["x"],
            players[players["hunter"]]["y"],
        ]
        wall = walls.get(wall)
        if is_wall_on_the_line(hunter, data_end, wall):
            return
    for id in players:
        if (
            players[id]
            and not isinstance(players[id], str)
            and id != players["hunter"]
        ):
            player = players[id]
            distanceToPlayer = math.sqrt(
                (player["x"] - players[players["hunter"]]["x"]) ** 2
                + (player["y"] - players[players["hunter"]]["y"]) ** 2
            )
            if distanceToPlayer > 150:
                continue
            distanceToClick = math.sqrt(
                (player["x"] - data["shot_x"]) ** 2
                + (player["y"] - data["shot_y"]) ** 2
            )
            if distanceToClick <= 10 and round_in_proccess is True:
                socket.emit(
                    "show_hit", {"x": player["x"], "y": player["y"], "id": id}
                )
                return


@socket.on("stop_timer_signal")
def stop_timer():
    db = next(get_db())
    global round_in_proccess, info
    round_in_proccess = False
    old_survivors_amount = info["total_survivors"]
    old_players = players.copy()
    if players["hunter"]:
        players[players["hunter"]]["role"] = "survivor"
        players["hunter"] = None
        info["total_hunters"] -= 1
        info["total_survivors"] += 1
        for i in players:
            if i != "hunter":
                user = (
                    db.query(User)
                    .filter(User.username == players[i]["username"])
                    .first()
                )
                user.games += 1
                db.add(user)
                db.commit()
                if not players[i]["is_alive"]:
                    players[i]["is_alive"] = True
                    info["total_survivors"] += 1
        if old_survivors_amount == 0:
            hunter = old_players["hunter"]
            username = players[hunter]["username"]
            user = db.query(User).filter(User.username == username).first()
            user.win_hunter += 1
            db.add(user)
            db.commit()
            socket.emit("hunter_win", info)
        else:
            hunter = old_players["hunter"]
            username = players[hunter]["username"]
            user = db.query(User).filter(User.username != username).all()
            for i in user:
                i.win_survivor += 1
                db.add(i)
                db.commit()
            socket.emit("survivors_win", info)
        socket.emit("update_all", players)
