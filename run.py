from utils import *
import telebot
import sys

TOKEN = config('TOKEN')

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")  # You can set parse_mode by default. HTML or MARKDOWN
handler = logging.StreamHandler(sys.stdout)
telebot.logger.addHandler(handler)
telebot.logger.setLevel(logging.WARNING)


def first_move_prompt(chat_id: int):
    prediction = api_call(1, [])
    bot.send_message(chat_id, "<b>Ход 1 (наш).</b> Кого забаним? Выбери или напиши имя героя 👇")

    # Варианты с низким риском
    keyboard = telebot.types.InlineKeyboardMarkup()
    buttons = [telebot.types.InlineKeyboardButton("{}".format(id2hero(hero["id"])), callback_data=hero["id"])
               for hero in prediction["low"]]
    keyboard.row(*buttons)
    bot.send_message(chat_id, "<b> Варианты с низким риском </b>",  reply_markup=keyboard)

    # Варианты со средним риском
    keyboard = telebot.types.InlineKeyboardMarkup()
    buttons = [telebot.types.InlineKeyboardButton("{}".format(id2hero(hero["id"])), callback_data=hero["id"])
               for hero in prediction["moderate"]]
    keyboard.row(*buttons)
    bot.send_message(chat_id, "<b> Варианты со средним риском </b>",  reply_markup=keyboard)

    # Варианты с высоким риском
    keyboard = telebot.types.InlineKeyboardMarkup()
    buttons = [telebot.types.InlineKeyboardButton("{}".format(id2hero(hero["id"])), callback_data=hero["id"])
               for hero in prediction["high"]]
    keyboard.row(*buttons)
    bot.send_message(chat_id, "<b> Варианты с высоким риском </b>", reply_markup=keyboard)


def prompt(chat_id: int):
    def build_keyboard():
        next_move = last_move_made(chat_id) + 1
        moves = chosen_heroes(chat_id)
        prediction = api_call(next_move, moves)

        keyboard = telebot.types.InlineKeyboardMarkup()
        buttons = [telebot.types.InlineKeyboardButton(id2hero(hero_id), callback_data=hero_id)
                   for hero_id in prediction if not is_hero_has_already_chosen(chat_id, hero_id)]
        keyboard.row(*buttons)

        return keyboard

    def build_text():
        if choosing_team_number == my_number(chat_id):
            part1 = "<b>Ход {} (наш).</b> ".format(move_number)
            if move_type == "ban":
                part2 = "Кого забаним? Выбери или напиши имя героя 👇"
            else:
                part2 = "Кого пикнем? Выбери или напиши имя героя 👇"
        else:
            part1 = "<b>Ход {} (их).</b> ".format(move_number)
            if move_type == "ban":
                part2 = "Кого они забанили? Напиши имя героя 👇"
            else:
                part2 = "Кого они пикнули? Напиши имя героя 👇"

        return part1 + part2

    move_number = last_move_made(chat_id) + 1
    choosing_team_number, move_type = get_next_move(chat_id)

    # Если первый ход - наш, то выводим свою, особенную подсказку
    if move_number == 1 and choosing_team_number == my_number(chat_id):
        return first_move_prompt(chat_id)

    choosing_team_number, move_type = get_next_move(chat_id)
    if choosing_team_number == my_number(chat_id):
        bot.send_message(chat_id, build_text(),  reply_markup=build_keyboard())
    else:
        bot.send_message(chat_id, build_text())


def final_message(chat_id):
    bot.send_message(chat_id, "🎉 <b>Драфт завершен!</b>")


@bot.message_handler(commands=['about'])
def about(message):
    hello_message = "👋 <b>Автор:</b> Гончаров Игорь, лицей 1557"
    bot.send_message(message.chat.id, hello_message)


@bot.message_handler(commands=['start', 'restart'])
def start(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton('Наш', callback_data='start_0'),
                 telebot.types.InlineKeyboardButton('Не наш', callback_data='start_1'))

    bot.send_message(message.chat.id, text='<b>Чей первый ход?</b>', reply_markup=keyboard)


@bot.message_handler(content_types=["text"])
def parse_answer(message):
    hero_id = get_hero(message.text)

    if hero_id == -1:  # Неизвестный ID или имя героя
        bot.send_message(message.chat.id, "🤷 Ничего не понятно, попробуй еще раз")
        return

    if is_hero_has_already_chosen(message.chat.id, hero_id):
        bot.send_message(message.chat.id, "🙅‍ Этого героя уже выбрали или забанили")
        return

    current_move = last_move_made(message.chat.id) + 1
    moves = chosen_heroes(message.chat.id)
    moves.append(hero_id)
    set_context(message.chat.id, {"last_move": current_move, "moves": moves})

    if is_last_move(current_move):
        final_message(message.chat.id)
    else:
        prompt(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def start_callback_query(call):
    if call.data == "start_0":
        set_context(call.message.chat.id, {"order": 0, "last_move": 0, "moves": []})
    elif call.data == "start_1":
        set_context(call.message.chat.id, {"order": 1, "last_move": 0, "moves": []})

    prompt(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def move_callback_query(call):
    message = call.message
    message.text = str(call.data)
    parse_answer(message)


if __name__ == '__main__':
    load_heroes()
    bot.infinity_polling()
