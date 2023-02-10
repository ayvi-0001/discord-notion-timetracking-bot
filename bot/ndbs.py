import os
import dotenv
from typing import Sequence

import notion

__all__: Sequence[str] = (
    'NDB_TIMETRACK',
    'NDB_ROLLUP',
    'NDB_OPTIONS',
)

dotenv.load_dotenv()

NDB_TIMETRACK = notion.Database(os.environ['NDB_TIMETRACK_ID'])
NDB_ROLLUP = notion.Database(os.environ['NDB_ROLLUP_ID'])
NDB_OPTIONS = notion.Database(os.environ['NDB_OPTIONS_ID'])
