import os
from datetime import datetime

from crescent.ext import tasks

import notion
from bot.utils import plugin


@plugin.include
@tasks.cronjob("10 0 * * *")
async def daily_rollup_page() -> None:
    # rollup page that time entries will relate to for totals.
    new_rollup_page = notion.Page.create(
        notion.Database(os.environ["NDB_ROLLUP_ID"]),
        page_title=f"{datetime.today().date()}",
    )

    dt = datetime.today().astimezone(new_rollup_page.tz)
    new_rollup_page.set_date("time_created", dt)
