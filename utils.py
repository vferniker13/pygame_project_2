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
