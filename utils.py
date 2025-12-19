from passlib.context import CryptContext
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

alphabet = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
]


def is_overlapping(
    new_wall: list[int],
    old_walls: dict,
    padding: int = 10,
    width: int = 15,
    height: int = 30,
) -> bool:
    x1, y1 = new_wall
    for num in old_walls:
        x2, y2 = old_walls[num]
        if (
            x1 + padding + width > x2
            and x1 < x2 + width + padding
            and y1 + padding + height > y2
            and y1 < y2 + height + padding
        ):
            return True
    return False


def is_obstacle_in_the_way(walls: dict, new_x: int, new_y: int) -> bool:
    for i in walls:
        wall = walls.get(i)
        if wall[0] <= new_x <= wall[0] + 15 and wall[1] <= new_y <= wall[1] + 30:
            return True
    return False


def generate_walls(amount: int) -> dict:
    old_walls = {}
    max_attempts = 100
    for i in range(amount):
        for attempt in range(max_attempts):
            x = random.randint(100, 800)
            y = random.randint(100, 750)
            new_wall = [x, y]
            if is_overlapping(new_wall, old_walls) is False:
                old_walls[i] = new_wall
                break
    return old_walls


def generate_random_color():
    color = "#"
    for i in range(6):
        color += random.choice(alphabet)
    return color


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def is_wall_on_the_line(begin_point: list[int], end_point: list[int], wall: list[int]):
    if (
        max(begin_point[0], end_point[0]) < wall[0]
        or min(begin_point[0], end_point[0]) > wall[0] + 15
    ):
        return False
    if (
        max(begin_point[1], end_point[1]) < wall[1]
        or min(begin_point[1], end_point[1]) > wall[1] + 30
    ):
        return False

    def sign(x, y):
        return (x - begin_point[0]) * (end_point[1] - begin_point[1]) - (
            y - begin_point[1]
        ) * (end_point[0] - begin_point[0])

    corners = [
        sign(wall[0], wall[1]),
        sign(wall[0] + 15, wall[1]),
        sign(wall[0] + 15, wall[1] + 30),
        sign(wall[0], wall[1] + 30)
    ]
    has_positive = any(c > 0 for c in corners)
    has_negative = any(c < 0 for c in corners)
    return has_positive and has_negative

