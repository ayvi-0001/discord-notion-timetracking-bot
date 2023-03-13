from typing import Sequence

import crescent
import hikari

import notion
from notion.query import *
from notion.exceptions.errors import NotionObjectNotFound
from notion.exceptions.errors import NotionValidationError

from bot.groups import *
from bot.notionDBids import *
from bot.nadict import NAdict
from bot.utils import plugin

__all__: Sequence[str] = (
    "create_time_entry_options",
    "autocomplete_time_entry_options",
    "autocomplete_active_timers",
    "session",
    "EntryListAdd",
    "EntryListDelete",
)


class _TimerCache:
    """Store's the autocomplete options for starting a new timer."""

    def __init__(self) -> None:
        self.timer_options: list[hikari.CommandChoice] = []


session = _TimerCache()


def create_time_entry_options() -> list[hikari.CommandChoice]:
    if not session.timer_options:
        query_results = (
            notion.Database(NDB_OPTIONS_ID)
            .query(filter_property_values=["lifetime_entries"])
            .get("results", [])
        )
        session.timer_options = []
        for result in query_results:
            e = NAdict(result)
            entry_name = e.properties.lifetime_entries.title_0_text.content
            session.timer_options.append(
                hikari.CommandChoice(name=str(entry_name), value=str(entry_name))
            )
        return session.timer_options
    else:
        return session.timer_options


# Query options table and create list at initial runtime.
create_time_entry_options()


# App command to refresh the options table
# if changes are made outside of the bot functions to add/delete options.
@plugin.include
@crescent.user_command(name="refresh-timesheet-entries", dm_enabled=True)
async def refresh_time_entry_options(ctx: crescent.Context, user: hikari.User):
    session.timer_options.clear()
    await ctx.respond(
        f"{ctx.user.mention} time entry options refreshed!", ephemeral=True
    )


# Autocomplete function only retrieves the session attribute,
# and re runs the function if it's empty.
# The query function and the autocomplete function are separated,
# otherwise the autocomplete in command takes too long to load.
async def autocomplete_time_entry_options(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    if not session.timer_options:
        create_time_entry_options()
    return session.timer_options


@plugin.include
@options.child
@crescent.command(
    name="add", description="Add a new option to the timesheet options database."
)
class EntryListAdd:
    page_title = crescent.option(str, description="Name to add to list.")

    async def callback(self, ctx: crescent.Context):
        NDB_OPTIONS = notion.Database(NDB_OPTIONS_ID)
        notion.Page.create(NDB_OPTIONS, page_title=self.page_title)
        await ctx.respond(f"Added a new option for `{self.page_title}`.")
        session.timer_options.clear()


@plugin.include
@options.child
@crescent.command(
    name="delete", description="Delete an option from the timesheet options database."
)
class EntryListDelete:
    page_title = crescent.option(str, description="Name to remove from list.")

    async def callback(self, ctx: crescent.Context):
        query_filter = PropertyFilter.text(
            "lifetime_entries", "title", "contains", self.page_title
        )

        try:
            result = notion.Database(NDB_OPTIONS_ID).query(
                payload=notion.build_payload(query_filter),
                filter_property_values=["lifetime_entries"],
            )

            block_id = [r["id"] for r in result.get("results", [])][0]
            notion.Block(str(block_id)).delete_self
            await ctx.respond(f"Deleted option for `{self.page_title}`.")
            session.timer_options.clear()

        except NotionObjectNotFound:
            await ctx.respond(f"Did not find an option for: `{self.page_title}`.")
        except NotionValidationError as e:
            await ctx.edit(f"{e}.")  # page is likely already archived.


async def autocomplete_active_timers(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    list_command_choices: list[hikari.CommandChoice] = []

    query_results = notion.Database(NDB_TIMETRACK_ID).query(
        payload=notion.build_payload(
            CompoundFilter()._and(
                PropertyFilter.checkbox("active", "equals", True),
                TimestampFilter.created_time("this_week", {}),
            ),
            SortFilter([EntryTimestampSort.created_time_descending()]),
        ),
        filter_property_values=["name", "id", "timer"],
    )

    if pages := query_results.get("results", []):
        for page in pages:
            page = NAdict(page)
            page_id, name, timer = (
                page.id,
                page.properties.name.title_0_text.content,
                page.properties.timer.formula.number,
            )

            list_command_choices.append(
                hikari.CommandChoice(
                    name=f"Category: {name} - Duration: {timer}", value=str(page_id)
                )
            )

        return list_command_choices

    else:
        return [hikari.CommandChoice(name="No active timers to display.", value="null")]
