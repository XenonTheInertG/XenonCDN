# (c) @AbirHasan2005

import os

class Config(object):
    API_HASH = "8c18d1c557a9ea40c9db53df6fcaa8a7"
    API_ID = 25382981
    BOT_OWNER = 6404372701
    BOT_TOKEN = "6621156447:AAE23JZ3AW5ULsb4tR4aFsBqlbgbl0F7u8A"
    BOT_USERNAME = "xenoncdnbot"
    DB_CHANNEL = -1002137218754
    LOG_CHANNEL = -1002137218754
    BANNED_USERS = set(int(x) for x in os.environ.get("BANNED_USERS", "1234567890").split())
    FORWARD_AS_COPY = True
    BROADCAST_AS_COPY = True
    BANNED_CHAT_IDS = list(set(int(x) for x in os.environ.get("BANNED_CHAT_IDS", "-1001362659779 -1001255795497").split()))
    OTHER_USERS_CAN_SAVE_FILE = True
    ABOUT_BOT_TEXT = f"""
    This is Permanent Files Store Bot!
    Send me any file I will save it in my Database. Also works for channel. Add me to channel as Admin with Edit Permission, I will add Save Uploaded File in Channel & add Sharable Button Link.

    Send me any file I will give you a permanent Sharable Link. I Support Channel Also! Check **About Bot** Button.
    """