import logging

import crescent
import hikari

INTENTS = hikari.Intents.ALL_PRIVILEGED | hikari.Intents.DM_MESSAGES | hikari.Intents.GUILD_MESSAGES

ayvi_bot_logger = logging.getLogger("ayvi-bot")
ayvi_bot_logger.setLevel(logging.INFO)
