import os
import dotenv
import asyncio
import logging
from datetime import datetime

import hikari
import miru
import crescent
from crescent.ext import tasks
from discord_webhook import AsyncDiscordWebhook
from discord_webhook import DiscordEmbed

from github import Github
from jsonpath_ng import parse

import notion
import notion.properties as prop
import notion.query as query

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv())

ayvi_bot_logger = logging.getLogger("ayvi-bot")
ayvi_bot_logger.setLevel(logging.INFO)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
WEBHOOK_NOTION_INTEGRATION = os.getenv('WEBHOOK_NOTION_INTEGRATION', '')
AYVIBOT_HELPER = os.getenv('AYVIBOT_HELPER', '')

TIMETRACK_DB = notion.Database(os.getenv('TIMETRACK_DB_ID', ''))
ROLLUP_DB = notion.Database(os.getenv('ROLLUP_DB_ID', ''))
OPTIONS_DB = notion.Database(os.getenv('OPTIONS_DB_ID', ''))

INTENTS = hikari.Intents.ALL_PRIVILEGED | hikari.Intents.DM_MESSAGES | hikari.Intents.GUILD_MESSAGES

bot = crescent.Bot(token=DISCORD_TOKEN, intents=INTENTS)

start = crescent.Group("start")
end = crescent.Group("end")
delete = crescent.Group("delete")
options = crescent.Group("options")
check = crescent.Group("check")


# ~~~~~ Runtime Operations ~~~~~


@bot.include
@crescent.event
async def on_ready(event: hikari.StartedEvent) -> None:
    content = f"ayvi-bot is online! heartbeat latency: {round(bot.heartbeat_latency, 5)} ms"
    ready = AsyncDiscordWebhook(url=AYVIBOT_HELPER, content=content, 
                                rate_limit_retry=True, timeout=10)
    ayvi_bot_logger.info(event)
    await ready.execute()

@bot.include
@crescent.event
async def send_terminal_event(event: hikari.ShardReadyEvent) -> None:
    ayvi_bot_logger.info(event)


# ~~~~~ Daily Operations ~~~~~


@bot.include 
@tasks.cronjob('0 4 * * *')
async def create_daily_rollup_page() -> None:
    # rollup page that time entries will relate to for totals.
    new_rollup_page = notion.Page.create(ROLLUP_DB, page_title=f"{datetime.today().date()}")
    new_rollup_page.set_date('time_created', datetime.today())


# ~~~~~ Start Timer ~~~~~


async def autocomplete_options(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    r = OPTIONS_DB.query(filter_property_values=['lifetime_entries'])
    # grabs plain_text key from name column in notion.
    entries = [m.value for m in parse("$.results[*].properties..plain_text").find(r)]
    list_options = [hikari.CommandChoice(name=e, value=e) for e in entries]
    return list_options


@bot.include
@start.child
@crescent.command(name="timer", description="Start new preset timer.")
class start_timer:
    category = crescent.option(str, "Select a time entry", autocomplete=autocomplete_options)

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f'Starting timer for {self.category}..', ephemeral=True, flags=16)

        new_timer = notion.Page.create(TIMETRACK_DB, page_title=self.category)
        
        rollup_category = f"rollup_{self.category}"
        timer_category = f"timer_{self.category}"
        sum_category = f"sum_{self.category}"
        
        try:
            # checks to see if a related column already exists.
            TIMETRACK_DB.property_schema[rollup_category]
        except KeyError:
            # creates a new one if not found, and notifies the function may take longer.
            await ctx.edit("Creating new rollup properties..")
            # synced property name key has some bugs with notion api at time of commit,
            TIMETRACK_DB.add_relation_column(ROLLUP_DB.id, ' ', property_name=rollup_category)
            # so have to rename the synced property from default separately.
            ROLLUP_DB.rename_property(f"Related to timetrack_db (rollup_{self.category})", timer_category)
            ROLLUP_DB.add_rollup_column(timer_category, 'timer', prop.FunctionsEnum.sum, property_name=sum_category)

        # query's rollup table for today's date to get id for related column.
        params = query.PropertyFilter.text('name', 'title', 'equals', f"{datetime.today().date()}")
        result = ROLLUP_DB.query(payload=params, filter_property_values=['name'])
        related_id = [match.value for match in parse("$.results[*].id").find(result)]
        new_timer.set_related(rollup_category, related_id)

        _content_page = f"New page created in `notion.Database('{new_timer.parent_id}')`"
        _content_id = f"New page ID: `{new_timer.id}`."
        content = f"{ctx.user.mention}\n{_content_page}\n{_content_id}"
        await ctx.followup(content) 


# ~~~~~ End Timer ~~~~~


async def autocomplete_active_timers(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    # query for active entries is limited to past week,
    # and filters properties returned to help reduce time.
    query_payload = notion.request_json(
        query.CompoundFilter(
            query.AndOperator(
                query.PropertyFilter.checkbox('active', 'equals', True),
                query.TimestampFilter.created_time('past_week', {}))),
            query.SortFilter([query.EntryTimestampSort.created_time_descending()]
            )
        )
    results = TIMETRACK_DB.query(payload=query_payload, 
                                 filter_property_values=['name','id','timer']
                                 ).get('results')

    list_responses = []
    if results:
        for obj in results:
            name = obj['properties']['name']['title'][0]['plain_text']
            id = obj['id'].replace('-','')
            timer = obj['properties']['timer']['formula']['number']
            display_name = f"Name: {name} | Duration: {timer}"
            list_responses.append(hikari.CommandChoice(name=display_name, value=id))
        return list_responses
    else:
        return [hikari.CommandChoice(name='No active timers to display.', value='null')]


@bot.include
@end.child
@crescent.command(name="timer", description="End any active timers.")
class EndTimer:
    active_timer = crescent.option(str, "Select an option to stop.", 
                                   autocomplete=autocomplete_active_timers)

    async def callback(self, ctx: crescent.Context) -> None:
        # without 'null' value, autocomplete search fails to load in discord.
        if self.active_timer == 'null':
            await ctx.respond(f"Nothing to stop!", ephemeral=True)
        else:
            await ctx.respond(f"Stopping timer...", ephemeral=True)
            active_page = notion.Page(self.active_timer)
            active_page.set_checkbox('end', True)
            await ctx.followup(f"Timer ended!")


# ~~~~~ Delete Page ~~~~~


@bot.include
@delete.child
@crescent.command(name='page', description='Delete the page associated with the input UUID.')
class delete_page_id:
    uuid = crescent.option(str, description='page id')

    async def callback(self, ctx: crescent.Context) -> None:
        notion.Block(self.uuid).delete_self
        await ctx.respond(f"Deleted `notion.Page('{self.uuid}')`.", ephemeral=True, flags=16) 


# ~~~~~ Entry List ~~~~~


@bot.include
@options.child
@crescent.command(name='add', description='Add a new option for dropdown entries')
class entry_list_add:
    page_title = crescent.option(str, description='Name to add to list.')

    async def callback(self, ctx: crescent.Context):
        notion.Page.create(OPTIONS_DB, page_title=self.page_title)
        await ctx.respond(f"Added a new option for {self.page_title}.", ephemeral=True)


@bot.include
@options.child
@crescent.command(name='delete', description='Delete an exisiting option from the dropdown entries')
class entry_list_delete:
    page_title = crescent.option(str, description='Name to remove from list.')

    async def callback(self, ctx: crescent.Context):
        params = notion.request_json(
            query.PropertyFilter.text('lifetime_entries', 'title', 'contains', self.page_title))
        response = OPTIONS_DB.query(payload=params, 
                                    filter_property_values=['lifetime_entries'])['results'][0]
        notion.Block(response['id']).delete_self()
        await ctx.respond(f"Deleted option for {self.page_title}.", ephemeral=True)


# ~~~~~ Other ~~~~~


@bot.listen()
async def links(event: hikari.MessageCreateEvent) -> None:
    if not event.is_human:
        return
    if event.content == "--status":
        await event.message.respond("https://discordstatus.com/")
    if event.content == "--notionupdates":
        await event.message.respond("https://www.notion.so/releases")
    if event.content == "--notionchangelog":
        await event.message.respond("https://developers.notion.com/page/changelog")


g = Github(os.getenv('GITHUB_TOKEN'))
repo_notion_api = g.get_user().get_repo('notion-api')
repo_discord_bot = g.get_user().get_repo('discord-notion-timetracking-bot')

async def embed_repo_notion_api():
    response = AsyncDiscordWebhook(url=AYVIBOT_HELPER, rate_limit_retry=True)
    embed = DiscordEmbed(title="AYVI-0001 / notion-api")
    embed.set_url(repo_notion_api.svn_url)
    embed.set_footer(text=f"Last updated at: {repo_discord_bot.updated_at}")
    embed.set_color('9146ff')
    embed.set_timestamp()
    response.add_embed(embed)
    await response.execute()

async def embed_discord_bot():
    response = AsyncDiscordWebhook(url=AYVIBOT_HELPER, rate_limit_retry=True)
    embed = DiscordEmbed(title="AYVI-0001 / discord-notion-timetracking-bot")
    embed.set_url(repo_discord_bot.svn_url)
    embed.set_footer(text=f"Last updated at: {repo_discord_bot.updated_at}")
    embed.set_color('9146ff')
    embed.set_timestamp()
    response.add_embed(embed)
    await response.execute()


@bot.include
@crescent.user_command
async def GithubRepos(ctx: crescent.Context, user: hikari.User):
    await ctx.respond(
        f"{ctx.user.mention}\nRepos for this bot, and the notion api wrapper used.")
    await embed_repo_notion_api()
    await embed_discord_bot()


class LinkRollupDB(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.LINK, 
                         label="Total Rollups", 
                         url=os.getenv('LINK_ROLLUP_DB'))

class LinkTimesheetDB(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.LINK, 
                         label="Time tracking", 
                         url=os.getenv('LINK_TIMESHEET'))

class LinkOptionsDB(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.LINK, 
                         label="Options", 
                         url=os.getenv('LINK_TIMESHEET_OPTIONS'))


@bot.include
@crescent.user_command
async def DatabaseLinks(ctx: crescent.Context, user: hikari.User):
    view = miru.View(timeout=60)
    view.add_item(LinkRollupDB())
    view.add_item(LinkTimesheetDB())
    view.add_item(LinkOptionsDB())
    await ctx.respond(f"{ctx.user.mention}\nLinks to Notion Databases:", components=view.build())


@bot.include
@check.child
@crescent.command(name="bot", description="...")
async def check_if_live(ctx: crescent.Context) -> None:
    await ctx.defer()
    await asyncio.sleep(2)
    if bot.is_alive:
        await ctx.respond("heyo")


# ~~~~~ Run ~~~~~


if __name__ == "__main__":
    miru.install(bot)
    bot.run(activity=hikari.Activity(
            name="RUNNING ON GCP",
            type=hikari.ActivityType.PLAYING),
        )
