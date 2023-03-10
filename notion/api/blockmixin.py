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
from functools import cached_property
from typing import Sequence
from typing import Optional
from typing import Union
from datetime import datetime
from datetime import tzinfo

from tzlocal import get_localzone
from pytz import timezone
from uuid import UUID

from notion.api._about import *
from notion.core.typedefs import *
from notion.api.client import _NotionClient
from notion.exceptions.errors import NotionObjectNotFound

__all__: Sequence[str] = ["_TokenBlockMixin"]


class _TokenBlockMixin(_NotionClient):
    """
    Any object you interact with in Notion;
    Databases/Pages/individual child blocks, are all considered 'Blocks'
    This class assigns common attributes among all three types.
    """

    def __init__(
        self,
        id: str,
        /,
        *,
        token: Optional[str] = None,
        notion_version: Optional[str] = None,
    ) -> None:
        super().__init__(token=token, notion_version=notion_version)

        self.tz = get_localzone()
        self.id = id.replace("-", "")

        try:
            UUID(self.id)
        except ValueError:
            __failed_instance__ = f"""
                {self.__repr__()} instatiation failed validation:
                id should be a valid uuid, instead was `'{self.id}'`"""
            raise NotionObjectNotFound(__failed_instance__)

    @cached_property
    def _block(self) -> JSONObject:
        """
        Same result as retrieve() for `notion.api.notionblock.Block`.
        If used with `notion.api.notionpage.Page` or `notion.api.notiondatabase.Database`,
        retrieves the page or database object from the blocks endpoint.
        """
        return self._get(self._block_endpoint(self.id))

    @property
    def type(self) -> str:
        return str(self._block["type"])

    @property
    def object(self) -> str:
        return str(self._block["object"])

    @property
    def has_children(self) -> bool:
        return bool(self._block["has_children"])

    @property
    def is_archived(self) -> bool:
        return bool(self._block["archived"])

    @property
    def parent_type(self) -> str:
        return str(self._block["parent"]["type"])

    @property
    def parent_id(self) -> str:
        _parent_id = self._block["parent"][self.parent_type]
        if _parent_id is True:
            # sets key to 'workspace' rather than 'True'
            _parent_id = self.parent_type
        else:
            _parent_id = _parent_id.replace("-", "")
        return str(_parent_id)

    def set_tz(self, tz: Union[tzinfo, str]) -> None:
        """
        :param timezone: (required) set default timezone.
            class default matches the Windows-configured timezone
            Use `pytz.all_timezones` to retrieve list of tz options.
            Pass either str or `pytz.timezone(...)`
        """
        if isinstance(tz, tzinfo):
            self.__setattr__("tz", tz)
        elif isinstance(tz, str):
            self.__setattr__("tz", timezone(tz))

    @property
    def last_edited_time(self) -> datetime:
        """
        Notion returns datetime ISO 8601, UTC.
        Class default matches the Windows-configured timezone.
        Change default timezone with method `set_tz(...)`
        """
        return datetime.fromisoformat(self._block["last_edited_time"]).astimezone(
            tz=self.tz
        )

    @property
    def created_time(self) -> datetime:
        """
        Notion returns datetime ISO 8601, UTC.
        Class default matches the Windows-configured timezone.
        Change default timezone with method `set_tz(...)`
        """
        return datetime.fromisoformat(self._block["created_time"]).astimezone(
            tz=self.tz
        )

    def __repr__(self) -> str:
        return f"notion.{self.__class__.__name__}('{self.id}')"
