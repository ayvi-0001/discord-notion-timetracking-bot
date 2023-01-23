# Metadata that controls how a database property behaves. 
# Each database property object contain the following; 
#  - The ID of the property, usually a short string of random letters and symbols.
#    Some automatically generated property types have special human-readable IDs. 
#    For example, all Title properties have an ID of "title".name, id, and  key corresponding 
#  - The name of the property as it appears in Notion.
#  - A key corresponding with the value of type. The value is an object containing 
#    type-specific configuration that controls the behavior of the property
# https://developers.notion.com/reference/property-object

import typing

from dataclasses import InitVar
from dataclasses import KW_ONLY
from pydantic.dataclasses import dataclass

from notion.properties.options import NumberEnum
from notion.properties.options import PropertyColors
from notion.properties.options import FunctionsEnum


__all__: typing.Sequence[str] = (
    "SingleRelationConfig", 
    "DualRelationConfig", 
    "RollupConfig", 
    "SelectConfig", 
    "MultiSelectConfig", 
    "StatusConfig", 
    "DateConfig", 
    "PeopleConfig", 
    "FilesConfig", 
    "CheckboxConfig", 
    "UrlConfig", 
    "EmailConfig", 
    "PhoneNumberConfig", 
    "FormulaConfig", 
    "CreatedTimeConfig", 
    "CreatedByConfig", 
    "LastEditedTimeConfig", 
    "LastEditedByConfig", 
    "PageTitleConfig", 
    "RichTextConfig", 
    "NumberConfig", 
    )


@dataclass(kw_only=False)
class SingleRelationConfig:
    database_id: InitVar[typing.Any]
    type: str = 'relation'
    relation: dict | None = None

    def __post_init__(self, database_id):
        self.relation = {"database_id":database_id,
                         "type":"single_property",
                         "single_property": {}}


@dataclass(kw_only=False)
class DualRelationConfig:
    database_id: InitVar[typing.Any]
    synced_property_name: InitVar[typing.Any]
    dual_property_config: typing.ClassVar = {}
    type: str = 'relation'
    relation: dict | None = None

    def __post_init__(
        self, database_id, synced_property_name, dual_property_config=dual_property_config
    ):
        dual_property_config.__setitem__('synced_property_name', synced_property_name)
        self.relation = {"database_id":database_id, 
                         "type":"dual_property",
                         "dual_property":dual_property_config}


@dataclass(kw_only=False)
class RollupConfig:
    rollup_property_name: InitVar[typing.Any]
    relation_property_name: InitVar[typing.Any]
    function: InitVar[FunctionsEnum]

    _: KW_ONLY
    type: str = 'rollup'
    rollup: dict | None = None

    def __post_init__(
        self, rollup_property_name, relation_property_name, function, 
    ):
        rollup_config = ({"rollup_property_name":rollup_property_name}
                       | {"relation_property_name":relation_property_name}
                       | {"function":function})
        self.rollup = rollup_config


@dataclass(kw_only=False)
class _DB_Option:
    name: str | None = None
    color: PropertyColors | None = None


@dataclass(kw_only=False)
class _DB_Group:
    name: str | None = None
    color: PropertyColors | None = None
    # option_ids:

    def __post_init__(self):
        self.color = PropertyColors.default if self.color is None else self.color


@dataclass(kw_only=False)
class SelectConfig:
    # option_id: InitVar[str | None] = None
    option_name: InitVar[str | None] = None
    option_color: InitVar[PropertyColors | None] = None

    _: KW_ONLY
    type: str = 'select'
    select: dict | None = None

    def __post_init__(self, option_name, option_color):
        options = _DB_Option(name=option_name, color=option_color)
        self.select = {"options":[options]}


@dataclass(kw_only=False)
class MultiSelectConfig:
    """
    assign options and groups in paranthesis

    Required:
    :param name: property name | NOTE: Commas , are not valid for options.

    Optional:
    :param id: option to update a multi-select property. or use name.
    :param color: defaults to <PropertyColors.default>
    """
    # option_id: InitVar[str | None] = None
    option_name: InitVar[str | None] = None
    option_color: InitVar[PropertyColors | None] = None

    _: KW_ONLY
    type: str = 'multi_select'
    multi_select: dict | None = None

    def __post_init__(self, option_name, option_color):
        options = _DB_Option(name=option_name, color=option_color)
        self.multi_select = {"options":[options]}


@dataclass(kw_only=False)
class StatusConfig:
    """assign options and groups in paranthesis.
    
    Options:
    
    Required:
    :param name: property name | NOTE: Commas , are not valid for options.

    Optional:
    :param id: option to update a multi-select property. or use name.
    :param color: defaults to <PropertyColors.default>
    
    Groups:
    
    Required:
    :param name: property name | NOTE: Commas , are not valid for options.

    Optional:
    :param color: defaults to <PropertyColors.default>

    Not Required:
    :param option_ids: array of string (UUID) | Sorted list of ids of all options that belong to a group.
    """
    # option_id: InitVar[str | None] = None
    option_name: InitVar[str | None] = None
    option_color: InitVar[PropertyColors | None] = None
    group_name: InitVar[str | None] = None
    group_color: InitVar[PropertyColors | None] = None

    _: KW_ONLY
    type: str = 'status'
    status: dict | None = None

    def __post_init__(self, option_name, option_color, group_name, group_color):
        options = _DB_Option(name=option_name, color=option_color)
        groups = _DB_Group(name=group_name, color=group_color)
        self.status = {"options":[options]} | {"groups":[groups]}


@dataclass
class DateConfig:
    type:str = 'date'
    date: dict | None = None

    def __post_init__(self): 
        self.date = {}


@dataclass
class PeopleConfig:
    type: str = 'people'
    people: dict | None = None

    def __post_init__(self):
        self.people = {}


@dataclass
class FilesConfig:
    type: str = 'files'
    files: dict | None = None

    def __post_init__(self):
        self.files = {}


@dataclass
class CheckboxConfig:
    type:str = 'checkbox'
    checkbox: dict | None = None

    def __post_init__(self):
        self.checkbox = {}


@dataclass
class UrlConfig:
    type: str = 'url'
    url: dict | None = None

    def __post_init__(self):
        self.url = {}


@dataclass
class EmailConfig:
    type: str = 'email'
    email: dict | None = None

    def __post_init__(self):
        self.email = {}


@dataclass
class PhoneNumberConfig:
    type: str = 'phonenumber'
    phone_number: dict | None = None

    def __post_init__(self):
        self.phone_number = {}


@dataclass(kw_only=False)
class FormulaConfig:
    """
    Required:
    :param expression: Formula expression in Notion.
    """
    expression: InitVar[typing.Any]
    
    _: KW_ONLY
    type: str = 'formula'
    formula: dict | None = None

    def __post_init__(self, expression):
        self.formula = {'expression':expression}


@dataclass
class CreatedTimeConfig:
    type: str = 'created_time'
    created_time: dict | None = None
    
    def __post_init__(self):
        self.created_time = {}


@dataclass 
class CreatedByConfig:
    type: str = 'created_by'
    created_by: dict | None = None
    
    def __post_init__(self):
        self.created_by = {}


@dataclass
class LastEditedTimeConfig:
    type: str = 'last_edited_time'
    last_edited_time: dict | None = None
    
    def __post_init__(self):
        self.last_edited_time = {}


@dataclass
class LastEditedByConfig:
    type: str = 'last_edited_by'
    last_edited_by: dict | None = None
    
    def __post_init__(self):
        self.last_edited_by = {}


@dataclass(kw_only=False)
class PageTitleConfig:
    type: str = 'title'
    title: dict | None = None
    
    def __post_init__(self):
        self.title = {}


@dataclass
class RichTextConfig:
    type: str = 'rich_text'
    rich_text: dict | None = None

    def __post_init__(self):
        self.rich_text = {}


@dataclass(kw_only=False)
class NumberConfig:
    number_format: InitVar[NumberEnum]
    
    _: KW_ONLY
    type: str = 'number'
    number: dict | None = None

    def __post_init__(self, number_format):
        self.number = {"format":number_format}

