from collections import OrderedDict
import math
import telebot
from telebot import types


token = "1175612452:AAESgXZEom1b4ZWLZxJV-zLy33SDBtqyL-0"

bot = telebot.TeleBot(token)
PLACE, PLACE_RESET, GEO, IMAGE, MENU, LIST, PLACE_LIST, PLACE_VIEW = range(8)
USER_STATE = {}
USER_VALUE = {}
USER_PLACE = {}

def get_distance(lat2, lon2, lat1, lon1):
    to_rad_koef = math.pi/180
    R = 6371;
    sin1 = math.sin((lat1 - lat2) * to_rad_koef / 2)

    sin2 = math.sin((lon1 - lon2) * to_rad_koef/ 2)
    return 2 * R * math.asin(math.sqrt(min(1, sin1 * sin1 + sin2 * sin2 * math.cos(lat1* to_rad_koef) * math.cos(lat2* to_rad_koef))))

def get_user_val(message):
    try:
        return USER_VALUE[message.chat.id]
    except KeyError:
        return "None"

def set_user_value(message, value):
    USER_VALUE[message.chat.id] = value

def get_state(message):
    try:
        return USER_STATE[message.chat.id]
    except KeyError:
        return MENU

def set_state(message, flag=MENU):
    USER_STATE[message.chat.id] = flag

def reset_place(message):
    USER_PLACE[message.chat.id] = OrderedDict()

def save_place(message, place):
    new_place = {place[0]: place}
    try:
         USER_PLACE[message.chat.id].update(new_place)
    except:
        USER_PLACE[message.chat.id] = OrderedDict(new_place)

    USER_PLACE[message.chat.id].move_to_end(place[0], last=False)
    if len(USER_PLACE[message.chat.id]) > 20:
        USER_PLACE[message.chat.id].popitem()



def get_place(message):
    return USER_PLACE[message.chat.id][message.text]

def get_image_url(photo):
    return f"https://api.telegram.org/file/bot{token}/{photo}"




@bot.message_handler(commands=["start", "help"])
def handle_message(message):
    text = """
    "Приветствую!
    Доступные команды:
    /add – добавление нового места
    /list – отображение добавленных мест
    /reset позволяет пользователю удалить все его добавленные локации
    /help - справка
    """
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=["add"])
def handle_message_add(message):
    bot.send_message(chat_id=message.chat.id, text="Укажите название места, которое хотите сохранить",
                     reply_markup=types.ReplyKeyboardRemove()
                     )
    set_state(message, PLACE)


@bot.message_handler(commands=["list"])
def handle_list(message):
    set_state(message, LIST)
    try:
        places = USER_PLACE[message.chat.id]
    except KeyError:
        bot.send_message(chat_id=message.chat.id, text="Вы еще не добавили ни одно место")
        handle_menu(message)
    else:
        if places:
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            button_geo = types.KeyboardButton(text="Ближайшие места", request_location=True)
            keyboard.add(button_geo)
            button_geo = types.KeyboardButton(text="Последние 10 мест")
            keyboard.add(button_geo)

            bot.send_message(message.chat.id, "Каике места хочешь посмотреть?",
                             reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text="Вы еще не добавили ни одно место")
            handle_menu(message)


@bot.message_handler(commands=["reset"])
def handle_message_reset(message):
    reset_place(message)
    bot.send_message(chat_id=message.chat.id, text="Вы очистили список мест",
                     reply_markup=types.ReplyKeyboardRemove()
                     )
    handle_menu(message)


@bot.message_handler(regexp="Отмена")
@bot.message_handler(func=lambda message: get_state(message) == MENU)
def handle_menu(message):

    set_state(message)

    set_user_value(message, None)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="/add")
    keyboard.add(button_geo)
    button_geo = types.KeyboardButton(text="/list")
    keyboard.add(button_geo)
    button_geo = types.KeyboardButton(text="/reset")
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, "Привет! Выбери команду)",
                     reply_markup=keyboard)


@bot.message_handler(content_types=["location"], func=lambda message: get_state(message)==LIST and not message.text)
def handle_place_list(message):
    lon = message.location.longitude
    lat = message.location.latitude
    try:
        place_list = (place for place in USER_PLACE[message.chat.id].values())
    except KeyError:
        bot.send_message(chat_id=message.chat.id, text="Вы еще не добавили ни одно место")
        handle_menu(message)

    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        near_count = 0
        for place in place_list:
            if get_distance(lat, lon, place[1]['lat'], place[1]['lon']) <0.55:
                near_count +=1
                button_geo = types.KeyboardButton(text=place[0])
                keyboard.add(button_geo)
        if near_count>0:
            bot.send_message(chat_id=message.chat.id, text=f"Вот список ближайших мест:",
                         reply_markup=keyboard
                         )
        else:
            bot.send_message(chat_id=message.chat.id, text="По близости нет сохраненных мест :(")
            handle_menu(message)

        set_state(message, PLACE_LIST)

@bot.message_handler(func=lambda message: get_state(message)==LIST and "Последние" in message.text)
def handle_place_list(message):
    try:
        place_list = (place for place in USER_PLACE[message.chat.id].values())
    except KeyError:
        bot.send_message(chat_id=message.chat.id, text="Вы еще не добавили ни одно место")
        handle_menu(message)

    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        for i, place in enumerate(place_list):
            if i == 10:
                break
            button_geo = types.KeyboardButton(text=place[0])
            keyboard.add(button_geo)

        bot.send_message(chat_id=message.chat.id, text=f"Вот список последних мест мест:",
                     reply_markup=keyboard
                     )
        set_state(message, PLACE_LIST)


@bot.message_handler(func=lambda message: get_state(message) == PLACE_LIST )
def handle_place_view(message):
    try:

        name, geo, photo = get_place(message)
    except KeyError:
        bot.send_message(message.chat.id, "что-то пошло не так, попробуйте еще раз")
    else:
        if photo:
            bot.send_photo(message.chat.id, photo, caption=name)
        else:
            bot.send_message(message.chat.id, name)
        bot.send_location(message.chat.id, geo["lat"], geo["lon"])
    handle_menu(message)



@bot.message_handler(func=lambda message: get_state(message) == PLACE )
def handle_geo(message):
    try:
        get_place(message)
    except KeyError:
        set_user_value(message, [message.text])
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_geo = types.KeyboardButton(text="Отправить текущее местоположение", request_location=True)
        keyboard.add(button_geo)
        button_cancell = types.KeyboardButton(text="Отмена")
        keyboard.add(button_cancell)
        bot.send_message(message.chat.id, "Отправь геолокацию или просто нажми на кнопку", reply_markup=keyboard)
        set_state(message, GEO)

    else:
        bot.send_message(message.chat.id, "Место с таким именем уже существует")
        handle_menu(message)



@bot.message_handler(func=lambda message: get_state(message) == GEO )
@bot.message_handler(content_types=["location"])
def location(message):
    if get_state(message) != GEO:
        bot.send_message(message.chat.id, text="Кажется геолокация отправилась некорректно, попробуй еще раз")
        handle_menu(message)
    elif message.location is not None:
        user_val = get_user_val(message)
        user_val.append({"lat":message.location.latitude,"lon":message.location.longitude})
        set_user_value(message, user_val)

        # print(message.location)
        # print("latitude: %s; longitude: %s" % (message.location.latitude, message.location.longitude))
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        button_cancell = types.KeyboardButton(text="Пропустить")
        keyboard.add(button_cancell)
        bot.send_message(message.chat.id, "Прикрепи изображение, если хочешь",
                         reply_markup=keyboard)

        set_state(message, IMAGE)




@bot.message_handler(content_types=["photo"], func=lambda message: get_state(message) == IMAGE)
def handle_image(message):

    photoID = message.photo[-1].file_id
    file = bot.get_file(photoID)
    file_path = file.file_path

    user_val = get_user_val(message)
    user_val.append(photoID)
    set_user_value(message, user_val)

    set_state(message, MENU)
    bot.send_message(chat_id=message.chat.id, text=f"место '{user_val[0]}' сохранено",
                     reply_markup=types.ReplyKeyboardRemove()
                     )

    # bot.send_location(message.chat.id, user_val[1]["lat"], user_val[1]["lon"] )
    save_place(message, user_val)
    set_user_value(message, None)
    handle_menu(message)

@bot.message_handler(func=lambda message: get_state(message) == IMAGE )
def handle_no_image(message):

    file_path = None

    user_val = get_user_val(message)
    user_val.append(file_path)
    set_user_value(message, user_val)

    set_state(message, MENU)
    bot.send_message(chat_id=message.chat.id, text=f"место '{user_val[0]}' сохранено")

    # bot.send_location(message.chat.id, user_val[1]["lat"], user_val[1]["lon"] )
    save_place(message, user_val)
    set_user_value(message, None)
    handle_menu(message)



if __name__ == '__main__':
  bot.polling()


