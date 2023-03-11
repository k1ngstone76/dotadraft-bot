import csv
import logging
from decouple import config
import requests

API_SERVER = config('API_SERVER')

# SCHEMA: текущая схема ходов для драфта
# (0, "ban")  - первый капитан банит героя
# (1, "pick") - второй капитан выбирает героя
SCHEMA = [(0,  "ban"), (1,  "ban"), (0,  "ban"), (1,  "ban"), (0,  "ban"), (1,  "ban"),
          (0, "pick"), (1, "pick"), (1, "pick"), (0, "pick"),
          (0,  "ban"), (1,  "ban"), (0,  "ban"), (1,  "ban"),
          (1, "pick"), (0, "pick"), (1, "pick"), (0, "pick"),
          (1,  "ban"), (0,  "ban"),
          (0, "pick"), (1, "pick")]

# CONTEXT: словарь словарей для хранения текущего контекста драфтов:
# {
#     "234324456": {            # chat ID
#         "order": 0,           # 0, если мы делаем первый ход в драфте, и 1 - если они
#         "last_move": 2,       # последний сделанный ход
#         "moves": [99, 101]    # герои, выбранные на предыдущих шагах драфта
#     },
#     "456456456": {
#         ...
#     },
#     ...
# }
CONTEXT = dict()

# HEROES_BY_ID: словарь для преобразования ID героя в имя:
# {
#     1: "Anti-Mage",
#     2: "Axe",
#     3: "Bane",
#     ...
# }
HEROES_BY_ID = dict()


# HEROES_BY_NAME: словарь для преобразования имени героя в ID. Имя хранится в lowercase:
# {
#     "anti-mage": 1,
#     "axe": 2,
#     "bane": 3,
#     ...
# }
HEROES_BY_NAME = dict()


# Загрузка словарей с героями из файла heroes.csv
def load_heroes() -> None:
    global HEROES_BY_ID
    global HEROES_BY_NAME

    with open("heroes.csv", "r") as f:
        csv_reader = csv.DictReader(f)
        for hero in csv_reader:
            hero_id, hero_name = int(hero["id"]), hero["name"]
            HEROES_BY_ID[hero_id] = hero_name
            HEROES_BY_NAME[hero_name.lower()] = hero_id


# Служебная функция для обращения к API
def api_call(move: int, body=None):
    if body is None:
        body = []
    url = "{}/{}".format(API_SERVER, move)
    resp = requests.post(url=url, json=body)

    res = resp.json()
    if resp.status_code != 200:
        logging.error('Got error status code from API: {}'.format(resp.status_code))
    elif res["status"] != "ok":
        logging.error('Got error from API ({}): {}'.format(res["status"], res["error"]))
    else:
        return res["prediction"]

    return []


# Преобразует имя героя в ID
def hero2id(hero_name: str) -> int:
    if hero_name.lower() == "nyx":
        hero_name = "Nyx Assassin"

    if hero_name.lower() in HEROES_BY_NAME.keys():
        res = int(HEROES_BY_NAME[hero_name.lower()])
    else:
        # Место для обработки сокращений, алиасов и пр.
        res = -1

    return res


# Преобразует ID в имя героя
def id2hero(hero_id: int) -> str:
    if hero_id in HEROES_BY_ID.keys():
        res = HEROES_BY_ID[hero_id]
    else:
        res = ""

    return res


def get_hero(s: str) -> int:
    hero_id = hero2id(s)

    if hero_id == -1:  # Такого имени не нашлось
        try:
            hero_id = int(s)
        except ValueError:
            hero_id = -1

        hero_name = id2hero(hero_id)
        if hero_name == "":  # Такого ID не нашлось
            hero_id = -1

    return hero_id


def set_context(chat_id, data):
    global CONTEXT
    if chat_id not in CONTEXT.keys():
        CONTEXT[chat_id] = {"order": -1, "last_move": -1, "moves": None}

    for k, v in data.items():
        CONTEXT[chat_id][k] = v


def my_number(chat_id):
    if chat_id in CONTEXT.keys():
        return CONTEXT[chat_id]["order"]
    else:
        return -1


def last_move_made(chat_id):
    if chat_id in CONTEXT.keys():
        return CONTEXT[chat_id]["last_move"]
    else:
        return 0


def chosen_heroes(chat_id):
    if chat_id in CONTEXT.keys():
        return CONTEXT[chat_id]["moves"]
    else:
        return None


def get_next_move(chat_id):
    return SCHEMA[last_move_made(chat_id)]


def is_last_move(i: int) -> bool:
    return i+1 > len(SCHEMA)


def is_hero_has_already_chosen(chat_id, hero_id):
    if chat_id in CONTEXT.keys():
        return hero_id in CONTEXT[chat_id]["moves"]

    return False
