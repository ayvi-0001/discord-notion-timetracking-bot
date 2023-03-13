import os
import dotenv
from typing import cast
from typing import Union
from typing import Sequence
from datetime import datetime

import tzlocal
import crescent
import hikari
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import notion
from notion.query import *
from notion.exceptions.errors import NotionValidationError
from bot.groups import *
from bot.nadict import NAdict
from bot.utils import plugin
from bot.schedule.scheduler import scheduler
from bot.schedule.reminders import DEFAULT_USER
from bot.schedule.reminders import notion_block_reminder
from bot.schedule.reminders import discord_reminder_channel_main

__all__: Sequence[str] = ["sync_cron"]


async def _delete_synced_cron_jobs(
    ctx: crescent.Context,
    scheduler: AsyncIOScheduler,
    job_id: str,
    page: notion.Page,
    dt_last_sync: datetime,
) -> None:
    page.set_status("sync", "syncing")
    scheduler.remove_job(job_id, jobstore="repeat")
    page.set_status("sync", "archived")
    page.set_checkbox("archive", False)
    page.set_date("last_synced", dt_last_sync)
    await ctx.respond(f"{ctx.user.mention} Archived page:`{page.id}` job: `{job_id}`")


async def _pause_synced_cron_jobs(
    ctx: crescent.Context,
    scheduler: AsyncIOScheduler,
    job_id: str,
    page: notion.Page,
    dt_last_sync: datetime,
) -> None:
    page.set_status("sync", "syncing")
    scheduler.pause_job(job_id, jobstore="repeat")
    page.set_status("sync", "paused")
    page.set_checkbox("pause", False)
    page.set_date("last_synced", dt_last_sync)
    await ctx.respond(
        "{}\n{}".format(
            f"{ctx.user.mention} Paused job `{job_id}`",
            "No further run times will be calculated for it until the job is resumed.",
        )
    )


async def _resume_paused_cron_jobs(
    ctx: crescent.Context,
    scheduler: AsyncIOScheduler,
    job_id: str,
    page: notion.Page,
    dt_last_sync: datetime,
) -> None:
    page.set_status("sync", "syncing")
    scheduler.resume_job(job_id, jobstore="repeat")
    page.set_status("sync", "active")
    page.set_date("last_synced", dt_last_sync)
    page.set_checkbox("resume", False)
    await ctx.respond(f"{ctx.user.mention} Resuming page:`{page.id}` job: `{job_id}`")


async def sync_crontasks_with_notion_db(
    ctx: crescent.Context, user_name: Union[str, None] = DEFAULT_USER
) -> None:
    NDB_JOBSTORE_CRON = notion.Database(os.environ["NDB_JOBSTORE_CRON_ID"])
    query = NDB_JOBSTORE_CRON.query()

    if query.get("results") != []:
        page_ids = [r["id"] for r in query.get("results", [])]
        for id in page_ids:
            page = notion.Page(id)

            dt_last_sync = cast(
                "datetime", datetime.now().astimezone(page.tz).isoformat()
            )

            _page = NAdict(page.properties)
            synced = _page.sync.status.name
            pause = _page.pause.checkbox
            resume = _page.resume.checkbox
            delete = _page.archive.checkbox

            if (
                "active" in synced
                and not any([delete, pause, resume])
                or "archived" in synced
            ):
                pass

            elif "active" in synced and delete:
                await _delete_synced_cron_jobs(
                    ctx=ctx,
                    scheduler=scheduler,
                    job_id=str(_page.job_id.rich_text_0_text.content),
                    page=page,
                    dt_last_sync=dt_last_sync,
                )

            elif "active" in synced and pause:
                await _pause_synced_cron_jobs(
                    ctx=ctx,
                    scheduler=scheduler,
                    job_id=str(_page.job_id.rich_text_0_text.content),
                    page=page,
                    dt_last_sync=dt_last_sync,
                )

            elif "paused" in synced and resume:
                await _resume_paused_cron_jobs(
                    ctx=ctx,
                    scheduler=scheduler,
                    job_id=str(_page.job_id.rich_text_0_text.content),
                    page=page,
                    dt_last_sync=dt_last_sync,
                )

            elif "queued" in synced and not any([delete, pause, resume]):
                try:
                    page.set_status("sync", "syncing")

                    crontab = _page.cron_expression.title_0_text.content
                    message = _page.message.rich_text_0_text.content
                    function_name = _page.function.select.name

                    if "notion" in function_name:
                        reminder_function = notion_block_reminder
                        fkwargs = {
                            "page_id": page.id,
                            "user_name": user_name,
                            "message": message,
                        }

                    elif "discord" in function_name:
                        reminder_function = discord_reminder_channel_main
                        fkwargs = {"message": message}

                    else:
                        error = f"`{page.__repr__()}` is missing a function to call."
                        await ctx.respond(error)
                        raise NotionValidationError(error)

                    trigger = CronTrigger.from_crontab(
                        crontab, timezone=tzlocal.get_localzone()
                    )

                    job = scheduler.add_job(
                        reminder_function,
                        trigger=trigger,
                        name=message,
                        jobstore="repeat",
                        executor="repeat",
                        kwargs=fkwargs,
                        misfire_grace_time=60,
                    )

                    page.set_status("sync", "active")
                    page.set_date("last_synced", dt_last_sync)
                    page.set_text("job_id", job.id)
                    page.set_text(
                        "jobstore", f"{scheduler._jobstores[job._jobstore_alias]}"
                    )

                    await ctx.respond(
                        f"Set `{page.__repr__()}` to active. Job ID: `{job.id}`"
                    )

                except AttributeError:
                    page.set_status("sync", "queued")
                    await ctx.respond(
                        "{} {} {}\n{} {}".format(
                            f"Failed to schedule reminder from",
                            f"`{NDB_JOBSTORE_CRON.__repr__()}`",
                            f" for `{page.__repr__()}`",
                            f"Check to see if `cron_expression` and `message` are filled out,",
                            "and that neither of them contain any mentions.",
                        ),
                        ephemeral=True,
                    )
            else:
                pass


@plugin.include
@crescent.user_command(name="sync-cron")
async def sync_cron(ctx: crescent.Context, user: hikari.User):
    await ctx.defer()
    await sync_crontasks_with_notion_db(ctx=ctx)
    await ctx.respond("Sync with `NDB_JOBSTORE_CRON` complete.", ephemeral=True)
