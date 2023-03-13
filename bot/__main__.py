import os
import dotenv

import crescent
import hikari
import miru
from discord_webhook import AsyncDiscordWebhook
from requests.exceptions import Timeout

from bot.schedule.scheduler import scheduler
from bot import bot_logger
from bot import INTENTS

dotenv.load_dotenv()

bot = hikari.GatewayBot(token=os.environ["DISCORD_TOKEN"], intents=INTENTS)

client = crescent.Client(app=bot)
client.plugins.load_folder("bot.schedule")
client.plugins.load_folder("bot.timer")
client.plugins.load_folder("bot.views")


@client.include
@crescent.event
async def on_ready(event: hikari.StartedEvent) -> None:
    bot_logger.info(event)
    try:
        webhook = AsyncDiscordWebhook(
            url=os.environ["WEBHOOK_URL_HELPER_BOT"],
            content=f"Online! heartbeat latency: {round(bot.heartbeat_latency, 5)} ms.",
            rate_limit_retry=True,
            timeout=10,
        )
        await webhook.execute()
    except Timeout:
        bot_logger.info(f"Discord connection timed out: {Timeout}")


@client.include
@crescent.event
async def terminal_event(event: hikari.ShardReadyEvent) -> None:
    bot_logger.info(event)


if __name__ == "__main__":
    miru.install(bot)
    scheduler.start()
    bot.run(
        activity=hikari.Activity(
            name="on gcp:compute engine", type=hikari.ActivityType.PLAYING
        )
    )
