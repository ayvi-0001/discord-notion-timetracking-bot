from typing import Sequence
from datetime import datetime

import crescent
import hikari
from crescent.ext import tasks

import notion

from bot.ndbs import *

plugin = crescent.Plugin[hikari.GatewayBot, None]()

__all__: Sequence[str] = ['create_daily_rollup_page',]

TODAY = f"{datetime.today().date()}"

@plugin.include 
@tasks.cronjob('0 0 * * *')
async def create_daily_rollup_page() -> None:
    # rollup page that time entries will relate to for totals.
    new_rollup_page = notion.Page.create(NDB_ROLLUP, page_title=TODAY)
    new_rollup_page.set_date('time_created', datetime.today())
