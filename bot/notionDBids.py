import os
import dotenv
from typing import Sequence

__all__: Sequence[str] = (
    "NDB_OPTIONS_ID",
    "NDB_TIMETRACK_ID",
    "NDB_ROLLUP_ID",
    "NDB_SCHEDULE_ID",
)

dotenv.load_dotenv()

NDB_TIMETRACK_ID = os.environ["NDB_TIMETRACK_ID"]
NDB_ROLLUP_ID = os.environ["NDB_ROLLUP_ID"]
NDB_OPTIONS_ID = os.environ["NDB_OPTIONS_ID"]
NDB_SCHEDULE_ID = os.environ["NDB_SCHEDULE_ID"]
