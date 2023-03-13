import os
import dotenv
from typing import Union
from typing import Sequence
from typing import Optional
from datetime import datetime

from discord_webhook import DiscordWebhook

import notion
import notion.properties as prop

from bot.utils import plugin
from bot.schedule.bqstore import retrieve_page_from_bq_store
from bot.schedule.bqstore import BQ_CACHE_TABLE_ID

__all__: Sequence[str] = (
    "notion_db_col_reminder",
    "notion_comment",
    "notion_block_reminder",
    "discord_reminder_channel_main",
    "DEFAULT_USER",
)

dotenv.load_dotenv()

WEBHOOK_URL_REMINDERS = os.environ["WEBHOOK_URL_REMINDERS"]

DEFAULT_USER = os.environ["DEFAULT_USER"]


# Appends 3 block children to the parent page, containing a user mention,
# a datetime stamp, and a message below.
def notion_block_reminder(
    page_id: str, message: str, user_name: Optional[str] = DEFAULT_USER
) -> None:
    target_page = notion.Page(page_id)
    mentionblock = notion.BlockFactory.paragraph(
        target_page,
        [
            prop.Mention.user(
                notion.Workspace.retrieve_user(user_name=user_name),
                annotations=prop.Annotations(
                    code=True, bold=True, color=prop.NotionColors.purple
                ),
            ),
            prop.RichText(" - "),
            prop.Mention.date(
                datetime.now().astimezone(target_page.tz).isoformat(),
                annotations=prop.Annotations(
                    code=True, bold=True, color=prop.NotionColors.purple_background
                ),
            ),
            prop.RichText(":"),
        ],
    )
    notion.BlockFactory.paragraph(mentionblock, [prop.RichText(message)])
    notion.BlockFactory.divider(target_page)


# Sets the `people` column of a database to the specified user, triggering a notification.
def notion_db_col_reminder(bq_id: str, user_name: Optional[str] = DEFAULT_USER) -> None:
    page = retrieve_page_from_bq_store(BQ_CACHE_TABLE_ID, bq_id)
    page.set_status("reminder_status", "complete")
    page.set_people(
        "notification", [notion.Workspace.retrieve_user(user_name=user_name)]
    )


# See `notion.api.workspace.Workspace` for comment operations.
def notion_comment(
    *,
    page: Optional[Union[notion.Page, notion.Block, str]] = None,
    message: str,
    user_name: Optional[str] = DEFAULT_USER,
) -> None:
    notion.Workspace.comment(
        page=page,
        rich_text=[
            prop.Mention.user(notion.Workspace.retrieve_user(user_name=user_name)),
            prop.RichText(" Reminder: "),
            prop.RichText(message),
        ],
    )


# Sends a single webhook containing the message.
# TODO Add channels/multiple urls.
def discord_reminder_channel_main(message: str) -> None:
    DiscordWebhook(url=WEBHOOK_URL_REMINDERS, content=message).execute()
