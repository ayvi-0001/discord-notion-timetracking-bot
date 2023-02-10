import asyncio
from typing import Sequence
from datetime import datetime

import crescent
import hikari
from jsonpath_ng.ext import parse

import notion
import notion.query as query
import notion.properties as prop

from bot.ndbs import *
from bot.groups import *

__all__: Sequence[str] = (
    'start_timer',
    'EndTimer',
    'delete_page_id',
    'entry_list_add',
    'entry_list_delete',
    'autocomplete_options',
    'autocomplete_active_timers',
    'update_daily_total',
    'daily_total',
    'live'
)


plugin = crescent.Plugin[hikari.GatewayBot, None]()

TODAY = f"{datetime.today().date()}"


# ~~~~~~~~~~     Start Timer     ~~~~~~~~~~


async def autocomplete_options(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:

    results = NDB_OPTIONS.query(filter_property_values=['lifetime_entries'])
    expr = "$.results[*].properties..plain_text"
    entries = [m.value for m in parse(expr).find(results)]
    list_options = [hikari.CommandChoice(name=e, value=e) for e in entries]

    return list_options


@plugin.include
@start.child
@crescent.command(
    name="timer", description="Start new preset timer."
)
class start_timer:
    category = crescent.option(
        str, "Select a time entry", autocomplete=autocomplete_options)

    async def callback(self, ctx: crescent.Context) -> None:

        await ctx.respond(f'Starting timer for {self.category}..', flags=16)

        new_timer = notion.Page.create(NDB_TIMETRACK, page_title=self.category)
        
        rollup_category = f"rollup_{self.category}"
        timer_category = f"timer_{self.category}"
        sum_category = f"sum_{self.category}"
        
        try:
            # checks to see if a related column already exists.
            NDB_TIMETRACK.property_schema[rollup_category]
        except KeyError:
            # creates a new one if not found, and notifies the function may take longer.
            await ctx.edit("Creating new rollup properties..")

            # synced property name key currently has some bugs with notion api,
            NDB_TIMETRACK.add_relation_column(NDB_ROLLUP.id, ' ', property_name=rollup_category)

            # so have to rename the synced property from default separately.
            default_name = f"Related to NDB_TIMETRACK (rollup_{self.category})"
            NDB_ROLLUP.rename_property(default_name, timer_category)

            NDB_ROLLUP.add_rollup_column(
                timer_category, 'timer', prop.FunctionsEnum.sum, property_name=sum_category
                )

        # query's rollup table for today's date to get id for related column.
        params = query.PropertyFilter.text('name', 'title', 'equals', TODAY)

        result = NDB_ROLLUP.query(payload=params, filter_property_values=['name'])
        related_id = [match.value for match in parse("$.results[*].id").find(result)]
        
        new_timer.set_related(rollup_category, related_id)

        _content_page = f"Started new timer for `{self.category}`!"
        _content_id = f"New page `uuid` ref: `{new_timer.id}`."
        content = f"{ctx.user.mention} {_content_page}\n{_content_id}"
        await ctx.edit(content) 


# ~~~~~~~~~~     End Timer     ~~~~~~~~~~


async def autocomplete_active_timers(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:

    filter_active = query.PropertyFilter.checkbox('active', 'equals', True)
    filter_created = query.TimestampFilter.created_time('past_week', {})
    sort = query.SortFilter([query.EntryTimestampSort.created_time_descending()])
    and_filter = query.AndOperator(filter_active, filter_created)
    compound = query.CompoundFilter(and_filter)
    query_payload = notion.request_json(compound, sort)

    results = NDB_TIMETRACK.query(payload=query_payload, 
                                  filter_property_values=['name','id','timer']
                                  ).get('results')

    list_command_choices: list[hikari.CommandChoice] = []

    if results:
        for obj in results:
            name = obj['properties']['name']['title'][0]['plain_text']
            id = obj['id'].replace('-','')
            timer = obj['properties']['timer']['formula']['number']
            display_name = f"Name: {name} | Duration: {timer}"
            list_command_choices.append(hikari.CommandChoice(name=display_name, value=id))
        return list_command_choices

    else:
        return [hikari.CommandChoice(name='No active timers to display.', value='null')]


async def update_daily_total(ctx: crescent.Context) -> None:
    filter = query.PropertyFilter.text('name', 'title', 'equals', TODAY)
    result = NDB_ROLLUP.query(payload=filter, filter_property_values=['total'])
    expr = "$.results[*].properties.total..number"
    total = [match.value for match in parse(expr).find(result)][0]

    await ctx.respond(
        f"{ctx.user.mention} | Updated daily total: **{total} hrs**", ephemeral=True
        ) 


@plugin.include
@end.child
@crescent.hook(update_daily_total, after=True)
@crescent.command(
    name="timer", description="End any active timers."
)
class EndTimer:
    active_timer = crescent.option(
        str, "Select an option to stop.", autocomplete=autocomplete_active_timers)

    async def callback(self, ctx: crescent.Context) -> None:

        # without 'null' value, autocomplete search fails to load in discord.
        if self.active_timer == 'null':
            await ctx.respond(f"{ctx.user.mention} Nothing to stop!")

        else:
            await ctx.respond(f"Stopping timer...")
            notion.Page(self.active_timer).set_checkbox('end', True)
            await ctx.edit(f"{ctx.user.mention} Timer ended! `uuid` ref: `{self.active_timer}`")


# ~~~~~~~~~~     Delete Page     ~~~~~~~~~~


@plugin.include
@delete.child
@crescent.command(
    name='page', description='Delete the page associated with the input UUID.'
)
class delete_page_id:
    uuid = crescent.option(str, description='page id')

    async def callback(self, ctx: crescent.Context) -> None:
        notion.Block(self.uuid).delete_self
        await ctx.respond(f"Deleted `notion.Page('{self.uuid}')`.", flags=16) 


# ~~~~~~~~~~     Entry List     ~~~~~~~~~~


@plugin.include
@options.child
@crescent.command(
    name='add', description='Add a new option for dropdown entries'
)
class entry_list_add:
    page_title = crescent.option(str, description='Name to add to list.')

    async def callback(self, ctx: crescent.Context):
        notion.Page.create(NDB_OPTIONS, page_title=self.page_title)
        await ctx.respond(f"Added a new option for {self.page_title}.")


@plugin.include
@options.child
@crescent.command(
    name='delete', description='Delete an exisiting option from the dropdown entries'
)
class entry_list_delete:
    page_title = crescent.option(str, description='Name to remove from list.')

    async def callback(self, ctx: crescent.Context):
        filter = query.PropertyFilter.text(
            'lifetime_entries', 'title', 'contains', self.page_title)

        response = NDB_OPTIONS.query(
            payload=notion.request_json(filter), 
            filter_property_values=['lifetime_entries'])['results'][0]
        
        notion.Block(response['id']).delete_self()
        await ctx.respond(f"Deleted option for {self.page_title}.")


# ~~~~~~~~~~     Other     ~~~~~~~~~~


@plugin.include
@daily.child
@crescent.command(
    name="total", description="Check total hours for today."
)
async def daily_total(ctx: crescent.Context) -> None:
    await ctx.respond(f"Checking total for today..")

    params = query.PropertyFilter.text('name', 'title', 'equals', TODAY)
    result = NDB_ROLLUP.query(payload=params, filter_property_values=['total'])
    expr = "$.results[*].properties.total..number"
    total = [match.value for match in parse(expr).find(result)][0]

    await ctx.edit(f"_{TODAY}_: **{total} hrs**") 


@plugin.include
@check.child
@crescent.command(
    name="bot", description="..."
)
async def live(ctx: crescent.Context) -> None:
    await ctx.defer()
    await asyncio.sleep(2)
    if plugin.app.is_alive:
        await ctx.respond("heyo")
