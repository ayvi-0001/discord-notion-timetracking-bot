import os
import dotenv
from typing import Sequence

from sqlalchemy.engine import create_engine
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from bot.utils import plugin

__all__: Sequence[str] = ["scheduler"]

dotenv.load_dotenv()


BQ_TABLE_REMINDERS = os.environ["BQ_TABLE_REMINDERS"]

BQ_TABLE_REPEATED = os.environ["BQ_TABLE_REPEATED"]

BQDATASET_APSCHEDULER_REMINDERS = os.environ["BQDATASET_APSCHEDULER_REMINDERS"]

BQDATASET_APSCHEDULER_REPEATED = os.environ["BQDATASET_APSCHEDULER_REPEATED"]

GOOGLE_APPLICATION_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

BQ_ENGINE_REMINDERS = create_engine(
    BQDATASET_APSCHEDULER_REMINDERS,
    credentials_path=GOOGLE_APPLICATION_CREDENTIALS,
)

BQ_ENGINE_REPEAT = create_engine(
    BQDATASET_APSCHEDULER_REPEATED,
    credentials_path=GOOGLE_APPLICATION_CREDENTIALS,
)

# main jobstore for one-time reminders, repeat jobstore for cron database.
scheduler = AsyncIOScheduler(
    jobstores={
        "main": SQLAlchemyJobStore(
            engine=BQ_ENGINE_REMINDERS, tablename=BQ_TABLE_REMINDERS
        ),
        "repeat": SQLAlchemyJobStore(
            engine=BQ_ENGINE_REPEAT, tablename=BQ_TABLE_REPEATED
        ),
    },
    executors={
        "main": ThreadPoolExecutor(20),
        "repeat": ThreadPoolExecutor(20),
        "processpool": ProcessPoolExecutor(10),
    },
)
