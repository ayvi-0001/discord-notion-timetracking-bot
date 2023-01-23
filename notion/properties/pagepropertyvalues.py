""" The endpoint limits the page response object to 25 references across all page properties. 
If a page object's Parent object is a database, then the property values conform to the database property schema. 
If a page object is not part of a database, then the only property value available for that page is its title.
2 types of responses: 
Retrieve a page endpoint response object (named_property), 
Retrieve a page property item endpoint response object (paginated list of results with values) 
Each page property value object contains a field 'type'.
The type of the property in the page object. Each type value has it's own object
e.g.

```
{
    "type": "property-type",
    "property-type": "type-specific value" # can be single value, bool, array, or another object
}
```
https://developers.notion.com/reference/page-property-values 
"""

import typing

from dataclasses import InitVar
from pydantic import Field
from pydantic.dataclasses import dataclass

from notion.properties.richtext import UserObject, RichText
from notion.properties.options import PropertyColors
from notion.properties.options import FunctionsEnum

__all__: typing.Sequence[str] = (
    "CheckBoxPropertyValue",
    "DatePropertyValue",
    "EmailPropertyValue",
    "NumberPropertyValue",
    "UrlPropertyValue",
    "RichTextPropertyValue",
    "PeoplePropertyValue",
    "Phone_NumberPropertyValue",
    "FormulaPropertyValue",
    "NotionUUID",
    "RelationPropertyValue",
    "SelectPropertyValue",
    "SelectOptions",
    "StatusPropertyValue",
    "RollupPropertyValue",
)


@dataclass(kw_only=False) 
class DatePropertyValue:
    """ 
    Required:
    :param start : If the "date" value is a range, then represents start of the range. 
    Optional:
    :param end: A string representing the end of a date range. 
                If the value is null, then the date value is not a range.
    https://developers.notion.com/reference/rich-text#date-mention-type-object 
    """
    start: InitVar[str]
    end: InitVar[str]
    type: str = Field(default='date')
    date: dict = Field(default_factory=dict)

    def __post_init__(self, start, end):
        self.date = {'start':start} | {'end':end}


@dataclass(kw_only=False) 
class FormulaPropertyValue:
    """
    NOTE: Formula value can't be updated directly via the API. 

    :classmethod bool:
    :classmethod date:
    :classmethod number:
    :classmethod string:
    """
    fvalue: InitVar[typing.Any]
    formulatype: InitVar[str]
    type: str = Field(default='formula')
    formula: dict = Field(default_factory=dict)

    def __post_init__(self, fvalue, formulatype):
        self.formula = {"type": formulatype} | {formulatype: fvalue}

    @classmethod
    def bool(cls, fvalue: bool, _formulatype='bool'):
        return cls(fvalue=fvalue, formulatype=_formulatype)
    
    @classmethod
    def date(cls, fvalue: DatePropertyValue, _formulatype='date'):
        return cls(fvalue=fvalue, formulatype=_formulatype)

    @classmethod
    def number(cls, fvalue: int, _formulatype='number'):
        return cls(fvalue=fvalue, formulatype=_formulatype)

    @classmethod
    def string(cls, fvalue: str, _formulatype='string'):
        return cls(fvalue=fvalue, formulatype=_formulatype)
    

@dataclass(kw_only=False) 
class NotionUUID:
    id: str | None = None


@dataclass(kw_only=False) 
class RelationPropertyValue:
    """An array of related page references. 
    A page reference is an object with an id key and a string value 
    (UUIDv4) corresponding to a page ID in another database.
    If a relation has more than 25 references, then the has_more
    value for the relation in the response object is true. 
    If a relation doesn't exceed the limit, then has_more is false. 
    """
    references: InitVar[list[NotionUUID]]
    type: str = Field(default='relation')
    relation: list[NotionUUID] | None = None
    has_more: bool = False

    def __post_init__(self, references):
        self.relation = references


@dataclass(kw_only=False) 
class EmailPropertyValue:
    type: str = Field(default='email')
    email: str | None = None


@dataclass(kw_only=False) 
class NumberPropertyValue:
    type: str = Field(default='number')
    number: int | None = None


@dataclass(kw_only=False) 
class UrlPropertyValue:
    type: str = Field(default='url')
    url: str | None = None


@dataclass(kw_only=False) 
class RichTextPropertyValue:
    """
    Required
    :param rich_text: reference to a :class:`RichText`

    Not Required
    :param type:

    The RichText object returns `type` as `text`.
    This class is for a few objects in Notion that require type `rich_text`
    """
    type: str = Field(default='rich_text')
    rich_text: RichText | None = None


@dataclass(kw_only=False) 
class PeoplePropertyValue:
    users: InitVar[list[UserObject]]
    type: str = Field(default='people')
    people: list | None = None

    def __post_init__(self, users):
        self.people = [users]


@dataclass(kw_only=False) 
class Phone_NumberPropertyValue:
    type: str = Field(default='phone_number')
    phone_number: str | None = None


@dataclass(kw_only=False) 
class CheckBoxPropertyValue:
    type: str = Field(default='checkbox')
    checkbox: bool = Field(default=None)


@dataclass(kw_only=False)
class SelectOptions:
    """Used by :class:`SelectPropertyValue` if creating multi_select object.
    """
    name: str | None = None
    color: PropertyColors | str | None = None


@dataclass
class SelectPropertyValue:
    """ 
    Call either single/multi classmethod.
    multi_select returns an array of selected options.
    ---
    Required
    :param name: Select option name. If the select database property doesn't 
                 have an option by that name yet, then the name is added to 
                 the database schema if the integration also has write access 
                 to the parent database.
    :param color: :class:`PropertyColors` Enum or string.
    """

    @classmethod
    def multi(cls, *options: SelectOptions, type:str = 'multi_select'):
        return ({'type': type} 
                | {'multi_select': [o for o in options]})

    @classmethod
    def single(cls, name: str, color: PropertyColors | str, type:str = 'select'):
        return ({'type': type} 
                | {'select': {'name':name, 'color':color}})


@dataclass(kw_only=False) 
class StatusPropertyValue:
    name: InitVar[str]
    color: InitVar[str]
    type: str = Field(default='status')
    status: dict = Field(default_factory=dict)

    def __post_init__(self, name, color):
        self.status = {'name':name, 'color':color}


@dataclass(kw_only=False) 
class RollupPropertyValue:
    """
    :param rollup: The value of the calculated rollup. 
                   The value can't be directly updated via the API.
    :param function: :class:`FunctionsEnum` or string
    """
    rollup_value: InitVar[str]
    type: str = Field(default='rollup')
    rollup: dict = Field(default_factory=dict)
    function: FunctionsEnum | str | None = None

    def __post_init__(self, rollup_value):
        self.rollup = {'type':'array',
                       'array':[rollup_value]}
