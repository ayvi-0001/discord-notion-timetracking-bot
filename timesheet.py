from __future__ import annotations

import time
import dotenv
import typing
import logging
from functools import reduce
from operator import getitem
from datetime import datetime 
from datetime import timedelta 

import numpy as np
import pandas as pd

import notion
import notion.query as query

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv())

start_time = time.time()

logger = logging.getLogger("notion-api")
logger.setLevel(logging.DEBUG)

TIMETRACK_DB = notion.Database('c20089127d6e4b63928ef5cdd9ae33e0')

DAYS_OF_WEEK = ['Sat', 'Fri', 'Thu', 'Wed', 'Tue', 'Mon', 'Sun']

TOTALS = pd.DataFrame(index=DAYS_OF_WEEK)

__all__: typing.Sequence[str] = (
    'weekly_totals',
    'entry_list',
    'TIMETRACK_DB',
    'TOTALS'
    )


def get_hours(db: notion.Database, client: str, delta: int) -> _ArrayNumber_co | None:
    filters = notion.request_json(construct_query(client, delta))
    response = db.query(filters).get('results')
    try:
        return weekly_hours_array(response)
    except KeyError:
        logger.debug(KeyError, "No results in Query")
        return None

def construct_query(client: str, delta: int) -> query.CompoundFilter:
    # function will run a cron job on discord bot each Sunday. Delta will iterate through week.
    dt_delta: str = (datetime.now() - timedelta(days=delta)).strftime("%Y-%m-%d")
    query_payload = query.CompoundFilter(
        query.AndOperator(
            query.PropertyFilter.date(
                'dt_created', 'date', 'equals', dt_delta, compound=True),
            query.PropertyFilter.text(
                'name', 'rich_text', 'contains', client.upper(), compound=True)
            )
        )
    return query_payload

def weekly_hours_array(query_response) -> _ArrayNumber_co:
    total = np.sum(np.append(np.array([]), 
                [x['properties']['timer']['formula']['number'] for x in query_response])
            )
    return total

def weekly_totals(time_entries) -> None:
    # Iterates through unique time entry names through the past 7 days.
    for client in time_entries:
        client_hours: list[_ArrayNumber_co | None] = []
        for days in enumerate(DAYS_OF_WEEK):
            client_hours.append(get_hours(db=TIMETRACK_DB, client=client, delta=days[0]+1))
        TOTALS[client] = client_hours

def entry_list(db: notion.Database) -> set[str]:
    list_results = [r for r in db.query().get('results')]
    title_keys = ['properties', 'name', 'title']
    _n_array = [reduce(getitem, title_keys, obj) for obj in list_results]
    _n_iter = [array[1][0] for array in enumerate(_n_array)]
    unique_names = set([name.get("plain_text").upper() for name in _n_iter])
    return unique_names


# annotations from :module:`numpy`
from numpy import bool_, number
ScalarType = typing.TypeVar("ScalarType", bound=np.generic, covariant=True)
NDArray = np.ndarray[typing.Any, np.dtype[ScalarType]]
_ArrayNumber_co = NDArray[typing.Union[bool_, number[typing.Any]]]


# E.g.
# weekly_totals(time_entries=entry_list(db=TIMETRACK_DB))
# print(TOTALS)
# print("--- %s seconds ---" % (time.time() - start_time))

#      CLIENT 1  CLIENT 2   CLIENT 3   CLIENT 4   CLIENT 5   CLIENT 6   CLIENT 7   CLIENT 8  PRODUCT DEVELOPMENT
# Sat  0.0       0.00       0.00       2.17       0.00       0.00       0.00       0.00      0.00
# Fri  0.0       0.00       0.22       3.95       2.45       0.20       0.00       0.00      0.18
# Thu  0.0       0.00       2.74       3.25       0.42       0.00       0.00       0.25      0.00
# Wed  0.0       0.00       2.33       0.37       0.00       0.75       0.00       3.31      0.00
# Tue  0.0       0.00       0.00       3.44       1.28       0.07       0.51       0.17      0.00
# Mon  0.0       1.72       3.35       0.00       0.96       0.00       0.00       0.00      0.00
# Sun  0.0       0.00       0.00       0.00       0.00       0.00       0.00       0.00      0.00
# --- 19.826013565063477 seconds ---
