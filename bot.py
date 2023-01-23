import os
import dotenv
import logging
import typing
import time
import asyncio

import crescent
from crescent.ext import tasks
import hikari
from discord_webhook import AsyncDiscordWebhook
from requests.exceptions import Timeout

import notion
import notion.query as query
from timesheet import *

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv())

logger = logging.getLogger("ayvi-bot")
logger.setLevel(logging.DEBUG)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WEBHOOK_NOTION_INTEGRATION = os.getenv('WEBHOOK_NOTION_INTEGRATION')
TIMETRACK_DB_ID = os.getenv('TIMETRACK_DB_ID')

TIMETRACK_DB = notion.Database(TIMETRACK_DB_ID)

INTENTS = (
    hikari.Intents.ALL_PRIVILEGED 
  | hikari.Intents.DM_MESSAGES 
  | hikari.Intents.GUILD_MESSAGES
)

start = crescent.Group("start")
queries = crescent.Group("queries")
end = crescent.Group("end")

bot = crescent.Bot(token=DISCORD_TOKEN, intents=INTENTS) #type: ignore


@bot.include
@crescent.event
async def on_ready(event: hikari.StartedEvent) -> None:
    logger.info(f"Bot Online. Latency: {round(bot.heartbeat_latency, 5)} ms")
    logger.info(event)


@bot.include
@crescent.event
async def send_terminal_event(event: hikari.ShardReadyEvent) -> None:
    logger.info(event)


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:
    if event.is_bot or not event.content:
        return
    else:
        logger.info(event)


@bot.include 
@tasks.cronjob('0 9 * * 0')
async def start_query_timesheet() -> None:
    notification = AsyncDiscordWebhook(
        url=WEBHOOK_NOTION_INTEGRATION, 
        content='Started query for weekly timesheet hours..')
    await notification.execute()
    # Query must run after await to avoid timeout. Est. time: 19.xx seconds.
    weekly_totals(time_entries=entry_list(db=TIMETRACK_DB))
 

@bot.include 
@tasks.cronjob('0 9 * * 0')
async def retrieve_query_timesheet() -> None:
    TIME_START = time.time()
    query_status = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                                       content=f"querying..")
    while TOTALS.empty:
        await query_status.execute()
        await asyncio.sleep(7)

    content = f"""----------------------------------
    > **__Your weekly timesheet:__**\n```{TOTALS}```
    **Query results:** _{round(time.time() - TIME_START, 3)}'s elapsed._
    """
    notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, content=content)
    await notification.execute()


ACTIVE_TIMER_ID: str


@bot.include
@start.child
@crescent.command(name='timer', description='Start new preset timer.')
async def start_timer(
    ctx: crescent.Context,
    category: typing.Annotated[str, crescent.Choices(
            hikari.CommandChoice(name="CLIENT 1", value="CLIENT 1"),
            hikari.CommandChoice(name="CLIENT 2", value="CLIENT 2"),
            hikari.CommandChoice(name="CLIENT 3", value="CLIENT 3"),
            hikari.CommandChoice(name="CLIENT 4", value="CLIENT 4"),
            hikari.CommandChoice(name="CLIENT 5", value="CLIENT 5"),
            hikari.CommandChoice(name="CLIENT 6", value="CLIENT 6"),
            hikari.CommandChoice(name="CLIENT 7", value="CLIENT 7"),
            hikari.CommandChoice(name="Product Development", value="Product Development"),
        ),
    ],
) -> None:
    new_page = notion.Page.blank(parent_instance=TIMETRACK_DB, content=category)
    
    global ACTIVE_TIMER_ID
    ACTIVE_TIMER_ID = new_page.id

    content = f"""
    Page created in `notion.Database('{new_page.parent_id}')`.\nnew_page = `notion.Page('{new_page.id}')`.
    """
    notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                               content=content, rate_limit_retry=True, timeout=10)
    await notification.execute()
    await ctx.respond(f'Timer started for `{category}`.', ephemeral=True, flags=16) 


@bot.include
@start.child
@crescent.command(name='custom', description='Start new custom timer.')
class start_custom:
    description = crescent.option(str, description='Page title')

    async def callback(self, ctx: crescent.Context) -> None:
        new_page = notion.Page.blank(parent_instance=TIMETRACK_DB, content=self.description)

        global ACTIVE_TIMER_ID
        ACTIVE_TIMER_ID = new_page.id
      
        content = f"""
        Page created in `notion.Database('{new_page.parent_id}')`.\nnew_page = `notion.Page('{new_page.id}')`.
        """
        notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                                   content=content, rate_limit_retry=True, timeout=10)
        await notification.execute()
        await ctx.respond(f'Timer started for `{self.description}`.', ephemeral=True, flags=16) 


@bot.include
@queries.child
@crescent.command(name='active', description='Query for any active timers.')
async def query_active(ctx: crescent.Context) -> None:
    query_payload = notion.payload(
        query.PropertyFilter.checkbox('active', 'equals', True))
    results = TIMETRACK_DB.query(data=query_payload).get('results')

    if results == []:
        await ctx.respond('No active timers found.')

    for obj in results:
        id =  obj['id'].replace('-','')
        name = obj['properties']['name']['title'][0]['plain_text']
        timer = obj['properties']['timer']['formula']['number']
        
        content = f"""
        Active timer:\nname: `{name}`\nobject: `notion.Page('{id}')`\ntimer: `{timer}`
        """
        await ctx.respond(content) 


@bot.include
@end.child
@crescent.command(name='active', description='End the active timer in the current session.')
async def end_active(ctx: crescent.Context) -> None:
    try:
        active_page = notion.Page(ACTIVE_TIMER_ID)
        active_page.update_checkbox('end', True)
        content = f"""
        `notion.Page('{active_page.id}')` in `notion.Database('{active_page.parent_id}')` updated.\nSet property item `end` to `True`.
        """
        notification = AsyncDiscordWebhook(
                url=WEBHOOK_NOTION_INTEGRATION, 
                content=content, rate_limit_retry=True, timeout=10)
        
        await ctx.respond(f'Timer Ended.', ephemeral=True, flags=16) 
        await notification.execute()
    except NameError:
        await ctx.respond(
            'No active timer set, or global variable unassigned.\nUse `/end id`.')


@bot.include
@end.child
@crescent.command(name='id', description='End the active timer with the associated id.')
class end_id:
    page_id = crescent.option(str, description='Retrieve with `/check active`.')

    async def callback(self, ctx: crescent.Context) -> None:
        active_page = notion.Page(self.page_id)
        active_page.update_checkbox('end', True)
        content = f"""
        `notion.Page('{self.page_id}')` in `notion.Database('{active_page.parent_id}')` updated.\nSet property item `end` to `True`.
        """
        notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                                           content=content, rate_limit_retry=True, timeout=10)
        await ctx.respond(f'Timer Ended.', ephemeral=True, flags=16) 
        await notification.execute()


if __name__ == "__main__":
    bot.run(
        activity=hikari.Activity(
        name=":RUNNING ON GCP:",
        type=hikari.ActivityType.PLAYING),
        asyncio_debug=True,             
        coroutine_tracking_depth=20,
        propagate_interrupts=True,
    )
