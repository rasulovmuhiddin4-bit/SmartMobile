from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    language = State()
    name = State()
    phone = State()
    location = State()

class AddAd(StatesGroup):
    brand = State()
    model = State()
    price = State()
    description = State()
    photo = State()

class ExchangeOffer(StatesGroup):
    wanted_brand = State()      # 1-qadam: kerakli brend
    wanted_model = State()       # 2-qadam: kerakli model
    offer_brand = State()        # 3-qadam: taklif brendi
    offer_model = State()        # 4-qadam: taklif modeli
    description = State()        # 5-qadam: tavsif

class Broadcast(StatesGroup):
    message = State()

class BlockUser(StatesGroup):
    user_id = State()