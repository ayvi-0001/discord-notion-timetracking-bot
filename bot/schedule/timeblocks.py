import re
from typing import Union
from typing import Sequence
from typing import Any

from dateutil import rrule
from datetime import datetime
from operator import methodcaller
from dateutil.relativedelta import relativedelta
import json

import crescent

import notion
from notion.query import *

from bot.groups import *
from bot.nadict import NAdict
from bot.notionDBids import *
from bot.utils import plugin

__all__: Sequence[str] = ["schedule_timeblocks"]


@plugin.include
@crescent.command(
    name="schedule-timeblocks",
    description="Creates timeblocks for any page in scheduler set to run.",
)
async def schedule_timeblocks(ctx: crescent.Context) -> None:
    await ctx.defer()

    scheduler = notion.Database(NDB_BOT_SCHEDULE_ID)
    query = scheduler.query(
        payload=notion.build_payload(
            PropertyFilter.status("status", "equals", "build next sync"),
            SortFilter([EntryTimestampSort.created_time_descending()]),
        ),
        filter_property_values=["name"],
    )
    query_result = query.get("results", [])

    if not query_result:
        await ctx.respond(
            "{} {}".format(
                "Did not find any timeblocks scheduled to run in",
                f"{scheduler.__repr__()}",
            )
        )

    else:
        schedule = notion.Database(NDB_SCHEDULE_ID)

        for page in query_result:
            _page = notion.Page(page["id"])
            _page.set_status("status", "building..")
            properties = _page.properties
            nproperties = NAdict(properties, sep=".")

            if not nproperties.rrule_freq:
                error = "{} {}".format(
                    "missing 1 required positional argument: 'freq'",
                    f"in {_page.__repr__()}",
                )
                await ctx.respond(error)
                raise ValueError(error)

            rules: rrule.rrule = rrule.rrule(**_map_rrule(nproperties))
            delta: relativedelta = relativedelta(**_map_relativedelta(nproperties))

            ndt_start: list[datetime] = list(rules)
            ndt_end: list[datetime] = [d + delta for d in ndt_start]
            dates: list[tuple[datetime, ...]] = [d for d in zip(ndt_start, ndt_end)]
            name: str = str(nproperties.name.title_0_text.content)

            page_content = NAdict(_page.retrieve_page_content())

            for d in dates:
                timeblock = notion.Page.create(schedule, page_title=str(name))
                timeblock.set_date(
                    "date",
                    start=d[0].astimezone(timeblock.tz),
                    end=d[1].astimezone(timeblock.tz),
                )

                try:
                    page_args = json.loads(
                        str(page_content.results_0_code.rich_text_0_text.content)
                    )
                    for a in page_args:
                        arg_method = methodcaller(
                            f"set_{page_args[a][0]}", a, page_args[a][1]
                        )
                        arg_method(timeblock)
                except AttributeError as e:
                    await ctx.respond(f"Error in {timeblock.__repr__()}: {e}")

            _page.set_status("status", "complete")
            _page.set_date("last_run", datetime.now().astimezone(_page.tz))

        await ctx.respond(f"Sync with schedule `{scheduler.__repr__()}` complete.")


def _extract_dt(d: dict, path: str) -> Union[datetime, None]:
    return datetime.fromisoformat(dtstart) if (dtstart := d.get(path)) else None


def _map_rrule(properties: NAdict) -> dict[str, Any]:
    freq = properties.get("rrule_freq.select.name")
    count = properties.get("rrule_count.number")
    dtstart = _extract_dt(properties, "rrule_dtstart.date.start")
    until = _extract_dt(properties, "rrule_until.date.start")
    interval = properties.get("rrule_interval.number")
    wkst = properties.get("rrule_wkst.select.name")
    bymonth = properties.get("rrule_bymonth.number")
    bymonthday = properties.get("rrule_bymonthday.number")
    byyearday = properties.get("rrule_byyearday.number")
    byweekno = properties.get("rrule_byweekno.number")
    byhour = properties.get("rrule_byhour.number")
    byminute = properties.get("rrule_byminute.number")
    byweekday = [
        eval(f"rrule.{v}")
        for k, v in properties.rrule_byweekday.items()
        if re.search("multi_select_._n.*", k)
    ]

    rrule_kwargs = {
        "count": count,
        "dtstart": dtstart,
        "until": until,
        "interval": interval,
        "bymonth": bymonth,
        "bymonthday": bymonthday,
        "byyearday": byyearday,
        "byweekno": byweekno,
        "byweekday": byweekday,
        "byhour": byhour,
        "byminute": byminute,
    }

    if freq:
        rrule_kwargs["freq"] = eval(f"rrule.{freq}")
    if wkst:
        rrule_kwargs["wkst"] = eval(f"rrule.{wkst}")

    return {k: v for k, v in rrule_kwargs.items() if v is not None}


def _map_relativedelta(properties: NAdict) -> dict[str, str]:
    days = properties.get("relativedelta_days.number")
    hours = properties.get("relativedelta_hours.number")
    minutes = properties.get("relativedelta_minutes.number")

    relativedelta_kwargs = {
        "days": days,
        "hours": hours,
        "minutes": minutes,
    }

    return {k: v for k, v in relativedelta_kwargs.items() if v is not None}
