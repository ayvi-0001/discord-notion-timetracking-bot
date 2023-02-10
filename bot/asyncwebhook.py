from typing import Sequence

from discord_webhook import AsyncDiscordWebhook
from requests.exceptions import Timeout

from bot import ayvi_bot_logger

__all__: Sequence[str] = ['async_webhook']

async def async_webhook(url, content):
    try:
        webhook = AsyncDiscordWebhook(
            url=url, content=content, rate_limit_retry=True, timeout=10
            )
        await webhook.execute()
    except Timeout:
        ayvi_bot_logger.info(f'Discord connection timed out: {Timeout}')
