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

INTENTS = (hikari.Intents.ALL_PRIVILEGED | hikari.Intents.DM_MESSAGES | hikari.Intents.GUILD_MESSAGES)

bot = crescent.Bot(token=DISCORD_TOKEN, intents=INTENTS) #type: ignore[assignmnent]

start = crescent.Group("start")
queries = crescent.Group("queries")
end = crescent.Group("end")
delete = crescent.Group("delete")


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


async def hook_timesheet_query(ctx: crescent.Context) -> None:
    await ctx.respond("Started query for weekly timesheet hours..")


@bot.include 
@tasks.cronjob('0 9 * * 0')
async def start_query_timesheet() -> None:
    notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
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
    category: typing.Annotated[
        str,
        crescent.Choices(
            hikari.CommandChoice(name="UBF", value="UBF"),
            hikari.CommandChoice(name="LON", value="LON"),
            hikari.CommandChoice(name="SOF", value="SOF"),
            hikari.CommandChoice(name="PFG", value="PFG"),
            hikari.CommandChoice(name="DBC", value="DBC"),
            hikari.CommandChoice(name="FWC", value="FWC"),
            hikari.CommandChoice(name="UBC", value="UBC"),
            hikari.CommandChoice(name="GAR", value="GAR"),
            hikari.CommandChoice(name="RYM", value="RYM"),
            hikari.CommandChoice(name="Product Development", value="Product Development"),
            hikari.CommandChoice(name="Training", value="Training"),
        ),
    ],
) -> None:
    new_page = notion.Page.create(TIMETRACK_DB, page_title=category)
    
    global ACTIVE_TIMER_ID
    ACTIVE_TIMER_ID = new_page.id

    content = f"""
    Page created in `notion.Database('{new_page.parent_id}')`.\nnew_page = `notion.Page('{new_page.id}')`.
    """
    hook = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                               content=content, rate_limit_retry=True, timeout=10)
    await ctx.respond(f'Timer started for `{category}`.', ephemeral=True, flags=16) 
    await hook.execute()


@bot.include
@start.child
@crescent.command(name='custom', description='Start new custom timer.')
class start_custom:
    description = crescent.option(str, description='Page title')

    async def callback(self, ctx: crescent.Context) -> None:
        new_page = notion.Page.create(TIMETRACK_DB, page_title=self.description)

        global ACTIVE_TIMER_ID
        ACTIVE_TIMER_ID = new_page.id
      
        content = f"""
        Page created in `notion.Database('{new_page.parent_id}')`.\nnew_page = `notion.Page('{new_page.id}')`.
        """
        hook = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                                   content=content, rate_limit_retry=True, timeout=10)
        await ctx.respond(f'Timer started for `{self.description}`.', ephemeral=True, flags=16) 
        await hook.execute()


@bot.include
@queries.child
@crescent.command(name='active', description='Query for any active timers.')
async def query_active(ctx: crescent.Context) -> None:
    query_payload = notion.request_json(
        query.PropertyFilter.checkbox('active', 'equals', True))
    results = TIMETRACK_DB.query(payload=query_payload).get('results')

    if results is None:
        await ctx.respond('No active timers found.')

    for obj in results:
        name = obj['properties']['name']['title'][0]['plain_text']
        id =  obj['id'].replace('-','')
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
        notification = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
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


@bot.include
@delete.child
@crescent.command(name='page_id', description='Delete the page associated with the input UUID.')
class delete_page_id:
    uuid = crescent.option(str, description='page id')

    async def callback(self, ctx: crescent.Context) -> None:
        page_as_block = notion.Block(self.uuid).delete_self

        content = f"""Deleted `notion.Page('{self.uuid}')`."""
        hook = AsyncDiscordWebhook(url=WEBHOOK_NOTION_INTEGRATION, 
                                   content=content, rate_limit_retry=True, timeout=10)
        await ctx.respond(f'Done!', ephemeral=True, flags=16) 
        await hook.execute()


@bot.listen()
async def test_listen(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human:
        return
    if event.content == "--status":
        await event.message.respond("https://discordstatus.com/")


if __name__ == "__main__":
    bot.run(
        activity=hikari.Activity(
        name=":ON AYVI PC:",
        type=hikari.ActivityType.PLAYING),
    )

# run with optimizations
# python -OO bot.py
