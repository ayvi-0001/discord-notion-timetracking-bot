# MIT License

# Copyright (c) 2023 ayvi#0001

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations
import os
from typing import Sequence
from typing import TypeAlias
from typing import Optional
from typing import Union

import requests
import orjson

from notion.core import *
from notion.exceptions import *
from notion.api._about import *
from notion.core.typedefs import *

__all__: Sequence[str] = ["_NotionClient"]


class _NotionClient:
    """Base Class to inherit: token, headers, requests, and endpoints."""

    def __init__(
        self, *, token: Optional[str] = None, notion_version: Optional[str] = None
    ) -> None:
        if token:
            self.token = token
        else:
            try:
                self.token = os.getenv("NOTION_TOKEN")
            except NameError:
                pass
            finally:
                if self.token is None:
                    raise NotionUnauthorized(
                        f"notion.{self.__class__.__name__} {__token_error__}"
                    )

        __auth__ = f"Bearer {self.token}"

        self.headers: dict[str, str] = {
            "Authorization": __auth__,
            "Accept": __content_type__,
            "Content-type": __content_type__,
            "Notion-Version": __notion_version__,
        }

        if notion_version is not None:
            self.headers["Notion-Version"] = notion_version

    NotionEndpoint: TypeAlias = str

    @staticmethod
    def _block_endpoint(
        object_id: Optional[str] = None,
        /,
        *,
        children: Optional[bool] = None,
        page_size: Optional[int] = None,
        start_cursor: Optional[str] = None,
    ) -> NotionEndpoint:
        object_id_ = f"/{object_id}" if object_id else ""
        children_ = "/children" if children else ""
        page_size_ = f"&page_size={page_size}" if page_size else ""
        start_cursor_ = f"&start_cursor={start_cursor}" if start_cursor else ""
        urlparam_ = ""
        if any([page_size, start_cursor]):
            urlparam_ = "?"

        return "{}blocks{}{}{}{}{}".format(
            __base_url__, object_id_, children_, urlparam_, start_cursor_, page_size_
        )

    @staticmethod
    def _database_endpoint(
        object_id: Optional[str] = None, /, *, query: Optional[bool] = False
    ) -> NotionEndpoint:
        object_id_ = f"/{object_id}" if object_id else ""
        query_ = "/query" if query else ""

        return f"{__base_url__}databases{object_id_}{query_}"

    @staticmethod
    def _pages_endpoint(
        object_id: Optional[str] = None,
        /,
        *,
        properties: Optional[bool] = False,
        property_id: Optional[str] = None,
    ) -> NotionEndpoint:
        object_id_ = f"/{object_id}" if object_id else ""
        properties_ = "/properties" if properties else ""
        property_id_ = f"/{property_id}" if property_id else ""

        return f"{__base_url__}pages{object_id_}{properties_}{property_id_}"

    def _get(
        self,
        url: NotionEndpoint,
        /,
        *,
        payload: Optional[Union[JSONObject, JSONPayload]] = None,
    ) -> JSONObject:
        if payload is None:
            response = orjson.loads(requests.get(url, headers=self.headers).text)
        else:
            if isinstance(payload, dict):
                payload = orjson.dumps(payload)
            response = orjson.loads(
                requests.post(url, headers=self.headers, json=payload).text
            )

        validate_response(response)
        return response

    def _post(
        self,
        url: NotionEndpoint,
        /,
        *,
        payload: Optional[Union[JSONObject, JSONPayload]] = None,
    ) -> JSONObject:
        if payload is None:
            response = orjson.loads(requests.post(url, headers=self.headers).text)
        else:
            if isinstance(payload, dict):
                payload = orjson.dumps(payload)
            response = orjson.loads(
                requests.post(url, headers=self.headers, data=payload).text
            )

        validate_response(response)
        return response

    def _patch(
        self, url: NotionEndpoint, /, *, payload: Union[JSONObject, JSONPayload]
    ) -> JSONObject:
        if isinstance(payload, dict):
            payload = orjson.dumps(payload)
        response = orjson.loads(
            requests.patch(url, headers=self.headers, data=payload).text
        )

        validate_response(response)
        return response

    def _delete(self, url: NotionEndpoint, /) -> JSONObject:
        response = orjson.loads(requests.delete(url, headers=self.headers).text)

        validate_response(response)
        return response
