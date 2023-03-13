import os
from typing import Sequence
import webbrowser

import crescent
import hikari
import miru

from bot.utils import plugin

__all__: Sequence[str] = ("DatabaseLinks",)


class PersistentViewNotionLinks(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @miru.button(
        label="Total Hours",
        custom_id=os.environ[
            "LINK_ROLLUP_DB"
        ],  # custon_id's necessary for persistent view.
    )
    async def rollupdblink(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        try:
            await ctx.respond("Opening link in default browser..", delete_after=True)
            webbrowser.open(os.environ["LINK_ROLLUP_DB"])
        except (OSError, webbrowser.Error) as e:
            await ctx.respond(
                f"{ctx.user.mention} Could not open link: {e}",
            )

    @miru.button(
        label="Timesheet",
        custom_id=os.environ[
            "LINK_TIMESHEET"
        ],  # custon_id's necessary for persistent view.
    )
    async def timesheetdblink(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        try:
            await ctx.respond("Opening link in default browser..", delete_after=True)
            webbrowser.open(os.environ["LINK_TIMESHEET"])
        except (OSError, webbrowser.Error) as e:
            await ctx.respond(
                f"{ctx.user.mention} Could not open link: {e}",
            )

    @miru.button(
        label="Timesheet Options",
        custom_id=os.environ[
            "LINK_TIMESHEET_OPTIONS"
        ],  # custon_id's necessary for persistent view.
    )
    async def optionsdblink(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        try:
            await ctx.respond("Opening link in default browser..", delete_after=True)
            webbrowser.open(os.environ["LINK_TIMESHEET_OPTIONS"])
        except (OSError, webbrowser.Error) as e:
            await ctx.respond(
                f"{ctx.user.mention} Could not open link: {e}",
            )


@plugin.include
@crescent.user_command(name="database-links")
async def DatabaseLinks(ctx: crescent.Context, user: hikari.User):
    view = PersistentViewNotionLinks()
    await ctx.respond(
        f"{ctx.user.mention}  Links to Notion Databases:", components=view.build()
    )
    await view.start()
