import os
import dotenv

import crescent
import hikari
import miru

from bot.asyncwebhook import async_webhook
from bot import ayvi_bot_logger
from bot import INTENTS

dotenv.load_dotenv()

GUILD_SNOWFLAKE = int(os.environ['DEFAULT_GUILD_ID'])
AYVIBOT_HELPER_WEBHOOK = os.environ['AYVIBOT_HELPER_WEBHOOK']

bot = hikari.GatewayBot(token=os.environ['DISCORD_TOKEN'], intents=INTENTS)
client = crescent.Client(app=bot)

client.plugins.load_folder("bot.timer")
client.plugins.load_folder("bot.cron")
client.plugins.load_folder("bot.views")


@client.include
@crescent.event
async def on_ready(event: hikari.StartedEvent) -> None:
    heartbeat = round(bot.heartbeat_latency, 5)
    content = f"ayvi-bot is online! heartbeat latency: {heartbeat} ms."
    ayvi_bot_logger.info(event)
    await async_webhook(AYVIBOT_HELPER_WEBHOOK, content)


@client.include
@crescent.event
async def terminal_event(event: hikari.ShardReadyEvent) -> None:
    ayvi_bot_logger.info(event)


miru.install(bot)
bot.run(activity=hikari.Activity(name="ON GCP",type=hikari.ActivityType.PLAYING))
