import os
import uuid
from typing import Sequence
from datetime import datetime

import crescent
import dateparser
from dateparser.conf import SettingValidationError

from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError

import notion
from notion.query import *
from bot.groups import *
from bot.utils import plugin
from bot.schedule.scheduler import scheduler
from bot.schedule.bqstore import store_serialized_page
from bot.schedule.bqstore import BQ_CACHE_TABLE_ID
from bot.schedule.reminders import DEFAULT_USER
from bot.schedule.reminders import notion_db_col_reminder
from bot.schedule.reminders import discord_reminder_channel_main

__all__: Sequence[str] = (
    "NotionDbColReminder",
    "DiscordReminderChannelMain",
    "GetAllJobs",
    "GetJob",
    "RemoveJob",
    "PauseJob",
)


@plugin.include
@reminder.child
@crescent.command(
    name="in-notion",
    description="Creates a reminder page in `bot.apscheduler.reminders`",
)
class NotionDbColReminder:
    date = crescent.option(str, description="Datetime trigger.")
    message = crescent.option(str, description="Message to send.")
    user = crescent.option(
        str,
        "User to send notification to. Defaults to primary user.",
        default=DEFAULT_USER,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f"{ctx.user.mention} Scheduling job..", ephemeral=True)

        try:
            date_trigger = dateparser.parse(
                self.date,
                settings={
                    "RELATIVE_BASE": datetime.now(),
                    "PREFER_DATES_FROM": "future",
                },
            )

        except (ValueError, TypeError, SettingValidationError) as e:
            await ctx.edit(f"{ctx.user.mention} An error was raised: {e}")

        bq_id = str(uuid.uuid4())

        job = scheduler.add_job(
            notion_db_col_reminder,
            trigger=DateTrigger(date_trigger),  # type: ignore
            name=self.message,
            jobstore="main",
            executor="main",
            replace_existing=True,
            kwargs={"bq_id": bq_id, "user_name": self.user},
            misfire_grace_time=60,
        )

        await ctx.edit(f"{ctx.user.mention} Scheduled Job: \n`{job.__str__()}`.")

        # Creates a page containing the job info for reference.
        # Reminder will trigger in this page at job runtime.
        page = notion.Page.create(
            notion.Database(os.environ["NDB_JOBSTORE_REMINDERS_ID"]),
            page_title=self.message,
        )
        page.set_text("job_id", job.id)
        page.set_status("reminder_status", "awaiting")
        page.set_date(
            "next_run_time",
            datetime.fromisoformat(str(job.next_run_time)).astimezone(page.tz),
        )
        # At job runtime, page object will be retrieved from store.
        store_serialized_page(
            _object=page,
            table_id=BQ_CACHE_TABLE_ID,
            job_id=job.id,
            page_id=page.id,
            bq_id=bq_id,
            description=self.message,
        )


@plugin.include
@reminder.child
@crescent.command(
    name="in-discord",
    description="Sends a webhook with the reminder in the channel `main`.",
)
class DiscordReminderChannelMain:
    date = crescent.option(str, description="Datetime trigger.")
    message = crescent.option(str, description="Message to send.")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f"{ctx.user.mention} Scheduling job..", ephemeral=True)

        try:
            date_trigger = dateparser.parse(
                self.date,
                settings={
                    "RELATIVE_BASE": datetime.now(),
                    "PREFER_DATES_FROM": "future",
                },
            )

        except (ValueError, TypeError, SettingValidationError) as e:
            await ctx.edit(f"{ctx.user.mention} An error was raised: {e}")

        job = scheduler.add_job(
            discord_reminder_channel_main,
            trigger=DateTrigger(date_trigger),  # type: ignore
            name=self.message,
            jobstore="main",
            executor="main",
            replace_existing=True,
            kwargs={"message": self.message},
            misfire_grace_time=60,
        )

        await ctx.edit(f"{ctx.user.mention} Scheduled Job: \n`{job.__str__()}`.")

        page = notion.Page.create(
            notion.Database(os.environ["NDB_JOBSTORE_REMINDERS_ID"]),
            page_title=self.message,
        )
        page.set_text("job_id", job.id)
        page.set_status("reminder_status", "sending in discord")
        page.set_date(
            "next_run_time",
            datetime.fromisoformat(str(job.next_run_time)).astimezone(page.tz),
        )


@plugin.include
@jobstores.child
@crescent.command(name="get-all-jobs", description="Search for all jobs in a jobstore.")
class GetAllJobs:
    jobstore = crescent.option(
        str,
        name="jobstore",
        description="Choose which jobstore to search.",
        choices=[("apscheduler_reminders", "main"), ("apscheduler_repeated", "repeat")],
    )

    async def callback(self, ctx: crescent.Context):
        await ctx.respond(f"{ctx.user.mention} Searching jobstore..", ephemeral=True)

        jobs = scheduler.get_jobs(jobstore=self.jobstore)
        all_job_details: str = ""

        if not jobs:
            await ctx.edit(f"{ctx.user.mention} No jobs found in jobstore.")
        else:
            # TODO find new method - Discord caps message at 2000 characters
            for job in jobs:
                all_job_details += "{}\n{}\n\n".format(
                    f"Job ID: {job.id}",
                    f"Details: {job.__str__()}",
                )
            await ctx.edit(f"{ctx.user.mention}\n```{all_job_details}```")


@plugin.include
@jobstores.child
@crescent.command(name="get-job", description="Search a jobstore for a job ID.")
class GetJob:
    jobstore = crescent.option(
        str,
        name="jobstore",
        description="Choose which jobstore to search.",
        choices=[("apscheduler_reminders", "main"), ("apscheduler_repeated", "repeat")],
    )
    job_id = crescent.option(str, name="job-id", description="ID in jobstore.")

    async def callback(self, ctx: crescent.Context):
        await ctx.respond(f"{ctx.user.mention} Searching for job..", ephemeral=True)
        job = scheduler.get_job(job_id=self.job_id, jobstore=self.jobstore)

        if not job:
            await ctx.edit(f"{ctx.user.mention} Job ID not found.")
        else:
            job_details = "{}\n{}\n{}\n{}\n\n".format(
                f"Job ID: {job.id}",
                f"Details: {job.__str__()}",
                f"Store: {scheduler._jobstores[job._jobstore_alias]}",
                f"Function Reference: {job.func_ref}",
            )

            await ctx.edit(f"{ctx.user.mention}\n```{job_details}```")


@plugin.include
@jobstores.child
@crescent.command(name="remove-job")
class RemoveJob:
    jobstore = crescent.option(
        str,
        name="jobstore",
        description="Choose which jobstore to search.",
        choices=[("apscheduler_reminders", "main"), ("apscheduler_repeated", "repeat")],
    )
    job_id = crescent.option(str, name="job-id", description="ID of job to remove.")

    async def callback(self, ctx: crescent.Context):
        await ctx.respond(f"{ctx.user.mention} Searching jobstore..", ephemeral=True)
        try:
            scheduler.remove_job(self.job_id, jobstore=self.jobstore)
            await ctx.edit(f"{ctx.user.mention} Removed job `{self.job_id}`")
        except JobLookupError as e:
            await ctx.edit(f"{ctx.user.mention}: {e}")


@plugin.include
@jobstores.child
@crescent.command(name="pause-job")
class PauseJob:
    jobstore = crescent.option(
        str,
        name="jobstore",
        description="Choose which jobstore to search.",
        choices=[("apscheduler_reminders", "main"), ("apscheduler_repeated", "repeat")],
    )
    job_id = crescent.option(str, name="job-id", description="ID of job to remove.")

    async def callback(self, ctx: crescent.Context):
        await ctx.respond(f"{ctx.user.mention} Searching jobstore..", ephemeral=True)
        try:
            scheduler.pause_job(self.job_id, jobstore=self.jobstore)
            await ctx.edit(
                "{}\n{} {}".format(
                    f"{ctx.user.mention} Paused job `{self.job_id}`",
                    "No further run times will be calculated for it",
                    "until the job is resumed.",
                )
            )
        except JobLookupError as e:
            await ctx.edit(f"{ctx.user.mention}: {e}")
