import os
from typing import Sequence, Optional, Any

import json
import requests
from pydantic import Field
from requests.models import Response
from pydantic.dataclasses import dataclass

from notion.core import *
from notion.properties import *
from notion.api._about import *

__all__: Sequence[str] = ["_NotionClient"]


class _NotionClient:
    """Base Class to inherit: token, headers, requests, and endpoints."""
    def __init__(self, token: Optional[str] = None, notion_version: Optional[str] = None):
        if token is not None:
            self.token = token
        else:
            try:
                self.token = os.getenv('NOTION_TOKEN') #type: ignore
            except NameError: 
                pass
            finally:
                if self.token is None:
                    assert token is not None, (
                    f"<{__class__.__name__}> Missing Token",
                    "Check if dotenv is configured and token is named 'NOTION_TOKEN'"
                    )
            
        self.headers: dict[str, str] = {
            "Authorization": f'Bearer {self.token}',
            "Content-type": __content_type__,
            "Notion-Version": __notion_version__,
        }

        if notion_version is not None:
            self.headers['Notion-Version'] = notion_version
        

    @staticmethod
    def _endpoint(
        type: notion_endpoints, 
        object_id: Optional[str] = None, 
        children: bool = False, 
        query: bool = False, 
        properties: bool = False,
        property_id: str | None = None
    ) -> str:

        base = __base_url__
        obj_id = f'/{object_id}'if object_id is not None else '' 
        child = f'/children'if children is True else ''
        props = f'/properties'if properties is True else ''
        prop_id = f'/{property_id}' if property_id is not None else ''
        qry = f'/query'if query is True else ''
        
        return f'{base}{type}{obj_id}{child}{props}{prop_id}{qry}'


    @staticmethod
    def get_cursor(response: Response) -> dict | Any:
        _response = json.loads(response.text)

        @dataclass(frozen=True)
        class DatabaseQuery:
            result: dict[str, str] = Field(default_factory=dict) 
            next_cursor: dict[str, str] = Field(default_factory=dict) 
        
        if _response.get('has_more') is True:
            _next_cursor = _asdict(Cursor(_response.get('next_cursor')))
            return DatabaseQuery(result = _response, next_cursor = _next_cursor)
        else:
            logging.info('No more pages in query, cursor was set to None')
            return DatabaseQuery(result = _response)
    

    def _get(self, url: str, data: Optional[Json[str]] = None, cursor: bool = False) -> Any:
        if data is None:
            r = requests.get(url=url, headers=self.headers)
            if cursor is True:
                return self.get_cursor(r)
        else:
            data=json.dumps(data) if isinstance(data, dict) else data
            r = requests.post(url=url, headers=self.headers, data=data)
            if cursor is True:
                return self.get_cursor(r)
        return json.loads(r.text)


    def _patch(self, url: str, data) -> Any:
        data=json.dumps(data) if isinstance(data, dict) else data
        r = requests.patch(url=url, headers=self.headers, data=data)
        return json.loads(r.text)


    def _delete(self, url: str) -> Any:
        r = requests.delete(url=url, headers=self.headers)
        return json.loads(r.text)


    def _post(self, url: str, data: Optional[Json[str]] = None, cursor: bool = False) -> Any:
        if data is None:
            r = requests.post(url=url, headers=self.headers)
            if cursor is True and json.loads(r.text).get('has_more') is True:
                return self.get_cursor(r)
        else:
            data=json.dumps(data) if isinstance(data, dict) else data
            r = requests.post(url=url, headers=self.headers, data=data)
            if cursor is True: 
                return self.get_cursor(r)
        return json.loads(r.text)
