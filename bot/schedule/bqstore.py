import os
import uuid
import dotenv
import pickle
import tzlocal
from typing import Sequence
from typing import Optional
from datetime import datetime

from google.cloud import bigquery

import notion
from bot.utils import plugin

__all__: Sequence[str] = (
    "bq_object_cache",
    "store_serialized_page",
    "retrieve_page_from_bq_store",
    "BQ_CACHE_TABLE_ID",
)

client = bigquery.Client()

dotenv.load_dotenv()

BQ_CACHE_TABLE_ID = os.environ["BQ_CACHE_TABLE_ID"]


def bq_object_cache(table_id: str) -> bigquery.Table:
    schema = [
        bigquery.SchemaField("date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("bq_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("job_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("page_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("object", "BYTES", mode="NULLABLE"),
        bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
    ]
    return bigquery.Table(table_id, schema=schema)


def store_serialized_page(
    _object: notion.Page,
    table_id: str,
    job_id: str,
    page_id: str,
    bq_id: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    rows_to_insert = [
        (
            # date
            datetime.now().astimezone(tzlocal.get_localzone()).date(),
            # bq_id
            str(uuid.uuid4()) if not bq_id else bq_id,
            # job_id
            str(job_id),
            # page_id
            str(page_id),
            # object
            pickle.dumps(_object, protocol=pickle.HIGHEST_PROTOCOL),
            # name
            _object.__repr__() if callable(getattr(_object, "__repr__")) else None,
            # type
            str(type(_object)),
            # description
            description if description else None,
        )
    ]
    client.insert_rows(bq_object_cache(table_id), rows_to_insert)


def retrieve_page_from_bq_store(table_id: str, bq_id: str) -> notion.Page:
    query = f"SELECT * FROM `{table_id}` WHERE bq_id LIKE '{bq_id}'"
    query_results = client.query(query, location="US").result()
    retrieve_object = list(query_results)[0].get("object")
    return pickle.loads(retrieve_object)
