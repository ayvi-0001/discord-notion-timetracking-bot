import asyncio
from typing import Sequence
from datetime import datetime

import crescent

import notion
from notion.query import *
import notion.properties as prop
from notion.exceptions.errors import NotionValidationError
from notion.exceptions.errors import NotionObjectNotFound

from bot.groups import *
from bot.notionDBids import *
from bot.nadict import NAdict
from bot.utils import plugin
from bot.timer.options import autocomplete_time_entry_options
from bot.timer.options import autocomplete_active_timers

__all__: Sequence[str] = (
    "TimerStart",
    "autocomplete_active_timers",
    "update_daily_total",
    "TimerEnd",
    "TimerDelete",
    "update_daily_total",
    "daily_total",
    "live",
)


@plugin.include
@timer.child
@crescent.command(name="start", description="Start a new timer.")
class TimerStart:
    category = crescent.option(
        str, "Select a new time entry", autocomplete=autocomplete_time_entry_options
    )

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f"Starting Timer..")

        ndb_timetrack = notion.Database(NDB_TIMETRACK_ID)
        new_timer = notion.Page.create(ndb_timetrack, page_title=self.category)

        await ctx.edit(
            "{}\n{}\n{}\n{}".format(
                f"{ctx.user.mention} New Timer:",
                f"**Category:** `{self.category}`",
                f"**uuid ref:** `{new_timer.id}`",
                f"[notion page]({new_timer.url})",
            )
        )

        rollup_category = f"rollup_{self.category}"
        timer_category = f"timer_{self.category}"
        sum_category = f"sum_{self.category}"

        ndb_rollup = notion.Database(NDB_ROLLUP_ID)

        try:
            # checking to see if a related column already exists.
            ndb_timetrack[rollup_category]
        except NotionObjectNotFound:
            # creating a new one if not found.
            ndb_timetrack.dual_relation_column(
                rollup_category, ndb_rollup.id, timer_category
            )
            ndb_rollup.rollup_column(
                sum_category, timer_category, "timer", prop.NotionFunctionFormats.sum
            )

            # adding new rollup property to total sum.
            expression = str(
                NAdict(ndb_rollup._property_schema).total.formula_expression
            )
            expression += f""" + prop("{sum_category}")"""
            ndb_rollup.formula_column("total", expression=expression)

        now = datetime.now().astimezone(new_timer.tz)

        # querying rollup table for today's date to get id for related column.
        query_filter = notion.build_payload(
            PropertyFilter.text("name", "title", "equals", now.date())
        )
        query_results = ndb_rollup.query(
            payload=query_filter, filter_property_values=["name"]
        )

        related_id = [str(NAdict(query_results).results_0_id)]
        new_timer.set_related(rollup_category, related_id)
        new_timer.set_date("override_start", now)


async def update_daily_total(ctx: crescent.Context) -> None:
    date = datetime.today().date()
    query_filter = notion.build_payload(
        PropertyFilter.text("name", "title", "equals", date)
    )

    query_result = notion.Database(NDB_ROLLUP_ID).query(
        payload=query_filter, filter_property_values=["total"]
    )

    _query_result = NAdict(query_result)
    total = _query_result.results_0_properties.total.formula.number

    await ctx.respond(
        "{} {}".format(
            f"{ctx.user.mention} {date}",
            f"daily total (hrs): **`{total}`**",
        )
    )


@plugin.include
@timer.child
@crescent.hook(update_daily_total, after=True)
@crescent.command(name="end", description="End an active timer.")
class TimerEnd:
    active_timer = crescent.option(
        str, "Select an option to stop.", autocomplete=autocomplete_active_timers
    )

    async def callback(self, ctx: crescent.Context) -> None:
        if self.active_timer == "null":
            await ctx.respond(f"{ctx.user.mention} Nothing to stop!", ephemeral=True)
        else:
            await ctx.respond(f"Stopping timer...")
            timer = notion.Page(self.active_timer)

            timer.set_checkbox("stop", True)
            timer.set_date("override_end", datetime.now(tz=timer.tz))

            await ctx.edit(
                f"{ctx.user.mention} Ended timer: `{self.active_timer}`.",
            )


@plugin.include
@timer.child
@crescent.command(name="delete", description="Delete a page by `uuid`.")
class TimerDelete:
    uuid = crescent.option(str, description="page id")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f"{ctx.user.mention} Deleting page..")

        try:
            timer = notion.Page(self.uuid)
            title = NAdict(timer.properties).name.title_0_text.content
            # removing related page, or total would continue to show in totals.
            timer.set_related(f"rollup_{title}", [])
            notion.Block(self.uuid).delete_self

            await ctx.edit(f"{ctx.user.mention} Deleted `{self.uuid}`.")

        except NotionObjectNotFound:
            await ctx.edit(
                f"{ctx.user.mention} No results found for `uuid`: `{self.uuid}`."
            )
        except NotionValidationError as e:
            await ctx.edit(f"{ctx.user.mention} {e}.")


@plugin.include
@timesheet.child
@crescent.command(name="daily-total", description="Check total hours for today.")
async def daily_total(ctx: crescent.Context) -> None:
    await ctx.respond(f"Checking total for today..")

    date = datetime.today().date()
    query_filter = notion.build_payload(
        PropertyFilter.text("name", "title", "equals", date)
    )

    result = notion.Database(NDB_ROLLUP_ID).query(
        payload=query_filter, filter_property_values=["total"]
    )
    total = NAdict(result).results_0_properties.total.formula.number
    await ctx.edit(f"{ctx.user.mention} _{date}_ daily total (hrs): **`{total}`**")


@plugin.include
@crescent.command(name="check-bot", description="...")
async def live(ctx: crescent.Context) -> None:
    await ctx.defer()
    await asyncio.sleep(2)
    if plugin.app.is_alive:
        await ctx.respond("heyo")
