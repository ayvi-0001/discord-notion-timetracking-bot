import os
from typing import Sequence

import crescent
import hikari
import miru
from github import Github

from discord_webhook import AsyncDiscordWebhook
from discord_webhook import DiscordEmbed

plugin = crescent.Plugin[hikari.GatewayBot, None]()

__all__: Sequence[str] = (
    'LinkRollupDB',
    'LinkTimesheetDB',
    'LinkOptionsDB',
    'DatabaseLinks',
    'GithubRepos',
    'embed_repo_notion_api',
    'embed_discord_bot',
)

AYVIBOT_HELPER_WEBHOOK = os.environ['AYVIBOT_HELPER_WEBHOOK']


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


@plugin.include
@crescent.user_command
async def DatabaseLinks(ctx: crescent.Context, user: hikari.User):
    view = miru.View(timeout=60)
    view.add_item(LinkRollupDB())
    view.add_item(LinkTimesheetDB())
    view.add_item(LinkOptionsDB())
    await ctx.respond(f"{ctx.user.mention}\nLinks to Notion Databases:", components=view.build())


g = Github(os.environ['GITHUB_TOKEN'])
repo_notion_api = g.get_user().get_repo('notion-api')
repo_discord_bot = g.get_user().get_repo('discord-notion-timetracking-bot')

async def embed_repo_notion_api():
    response = AsyncDiscordWebhook(
        url=AYVIBOT_HELPER_WEBHOOK, rate_limit_retry=True)
    
    embed = DiscordEmbed(title="AYVI-0001 / notion-api")
    
    embed.set_url(repo_notion_api.svn_url)
    embed.set_footer(text=f"Last updated at: {repo_discord_bot.updated_at}")
    embed.set_color('9146ff')
    embed.set_timestamp()

    response.add_embed(embed)
    await response.execute()

async def embed_discord_bot():
    response = AsyncDiscordWebhook(
        url=AYVIBOT_HELPER_WEBHOOK, rate_limit_retry=True)
    
    embed = DiscordEmbed(title="AYVI-0001 / discord-notion-timetracking-bot")
    
    embed.set_url(repo_discord_bot.svn_url)
    embed.set_footer(text=f"Last updated at: {repo_discord_bot.updated_at}")
    embed.set_color('9146ff')
    embed.set_timestamp()

    response.add_embed(embed)
    await response.execute()


@plugin.include
@crescent.user_command
async def GithubRepos(ctx: crescent.Context, user: hikari.User):
    await ctx.respond(
        f"{ctx.user.mention}\nRepos for this bot, and the notion api wrapper used.")
    await embed_repo_notion_api()
    await embed_discord_bot()


# @plugin.app.listen()
# async def links(event: hikari.MessageCreateEvent) -> None:
#     if not event.is_human:
#         return
#     if event.content == "--status":
#         await event.message.respond("https://discordstatus.com/")
#     if event.content == "--notionupdates":
#         await event.message.respond("https://www.notion.so/releases")
#     if event.content == "--notionchangelog":
#         await event.message.respond("https://developers.notion.com/page/changelog")
