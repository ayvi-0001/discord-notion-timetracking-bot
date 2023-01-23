from __future__ import annotations

import typing
from functools import cached_property
from datetime import datetime

from pytz import timezone
from pydantic.dataclasses import dataclass

from notion.core import *
from notion.properties import *
from notion.api.client import _NotionClient

__all__: typing.Sequence[str] = ["_BaseNotionBlock"]

DEFAULT_TIMEZONE = 'PST8PDT'


class _BaseNotionBlock(_NotionClient):
    """All objects you interact with in Notion are considered 'Blocks'; 
    Databases, Pages, or the individual child blocks in a page. 

    Class assigns basic attributes common among all three types.

    The current version of Notion's API does not allow creating
    objects at the workspace level, and require a parent id.
    Subclasses use this for validation.
    """
    def __init__(
        self, id: str, token: str | None = None, notion_version: str | None = None
    ):
        super().__init__(token=token, notion_version=notion_version)

        self.id = str(id).replace('-','')
        self.default_tz = DEFAULT_TIMEZONE

    @cached_property
    def block_obj(self) -> typing.Any:
        """Returns the Block, Page, or Database from the 'retrieve blocks endpoint'."""
        url = super()._endpoint('blocks', object_id=self.id)
        return super()._get(url)
    
    @property
    def type(self) -> str:
        return self.block_obj['type']
    
    @property
    def object(self) -> str:
        return self.block_obj['object']

    @property
    def has_children(self) -> bool:
        return self.block_obj['has_children']

    @property
    def is_archived(self) -> bool:
        return self.block_obj['archived']
    
    @property
    def parent_type(self) -> bool:
        return self.block_obj['parent'].get('type')

    @property
    def parent_id(self) -> typing.Any:
        _parent_id = self.block_obj['parent'].get(self.parent_type)
        # return 'workspace' rather than returning True
        # e.g. workspace {"parent":{"type":"workspace","workspace":true}}
        if _parent_id is True:
            _parent_id = self.parent_type
        else:
            _parent_id = _parent_id.replace('-','')
        return _parent_id

    def set_default_tz(self, timez: pytz_timezone | str) -> None:
        """ 
        Required:
        :param timez: set default timezone. class default = 'PST8PDT'
                      Use pytz.all_timezones to retrieve list of tz options.
                      Pass either string or pytz.timezone(...)
        """
        self.__setattr__('default_tz', timez)

    @property
    def last_edited(self):
        """Notion returns datetime ISO 8601, UTC. 
        Class uses UTC-8:00 ('PST8PDT') as default.
        Change default timezone by calling set_default_tz(...)
        
        Access values with datetime attributes:
        example_block.last_edited.date
        example_block.last_edited.time
        """
        _last_edit = self.block_obj.get('last_edited_time')
        _dt = datetime.fromisoformat(
            _last_edit).astimezone(tz=timezone(self.default_tz)) 

        @dataclass(frozen=True)
        class LastEdit:
            date = _dt.strftime("%m/%d/%Y")
            day = _dt.strftime("%d")
            month = _dt.strftime("%m")
            year = _dt.strftime("%Y")
            time = _dt.strftime("%H:%M:%S")

        return LastEdit()

    @property
    def created(self):
        """Notion returns datetime ISO 8601, UTC. 
        Class uses UTC-8:00 ('PST8PDT') as default.
        Change default timezone by calling set_default_tz(...)
        
        Access values with datetime attributes:
        example_block.created.date
        example_block.created.time
        """
        _created_time = self.block_obj.get('created_time')
        _dt = datetime.fromisoformat(
            _created_time).astimezone(tz=timezone(self.default_tz)) 

        @dataclass(frozen=True)
        class CreatedTime:
            date = _dt.strftime("%m/%d/%Y")
            day = _dt.strftime("%d")
            month = _dt.strftime("%m")
            year = _dt.strftime("%Y")
            time = _dt.strftime("%H:%M:%S")

        return CreatedTime()

    def __repr__(self):
        return f'{self.__class__.__name__.lower()}_{self.id}'
