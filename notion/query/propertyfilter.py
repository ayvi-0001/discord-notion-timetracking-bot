""" Property filter object
Each database property filter object must contain a property key and a key corresponding 
with the type of the database property identified by property. 
The value is an object containing a type-specific filter condition.
"""

import typing

import dataclasses
import pydantic
from pydantic.dataclasses import dataclass

from notion.query.conditions import *

__all__: typing.Sequence[str] = ["PropertyFilter"]


@dataclass(kw_only=False) 
class PropertyFilter:
    """
    Each database property filter object must contain a property key and a key 
    corresponding with the type of the database property identified by property. 
    The value is an object containing a type-specific filter condition.
    https://developers.notion.com/reference/post-database-query-filter#property-filter-object

    Required
    :param pname: name of the property as it appears in Notion.
    :param ptype: type of property object - only requires manual input for text/date/people.
    :param fval: value to filter on.
    :param fcon: logical conditions to apply filter on.


    Example use:
    ```python
    filter = notion.payload(
        query.PropertyFilter.checkbox(
            pname='input prop name', fcon=query.CheckboxFilter.equals, fval=False)
            )
    # out:
    ```
    ```json
    {
        "filter": {
            "property": "input prop name",
            "checkbox": {
                "equals": true
            }
        }
    }
    ```
    """
    pname: dataclasses.InitVar[typing.Any]
    ptype: dataclasses.InitVar[typing.Any]
    fcon: dataclasses.InitVar[typing.Any]
    fval: dataclasses.InitVar[typing.Any]
    filter: dict = pydantic.Field(default_factory=dict)

    def __post_init__(self, pname, ptype, fcon, fval):
        self.filter = ({'property': pname} | {ptype: {fcon: fval}})

    @property
    def compound(self):
        return list(dataclasses.asdict(self).values())[0]
        # If combining with compounded filters, we need to drop the first key 'filter'.

    @classmethod
    def rollup(cls, pname: str, fcon: RollupConditions, fval, ptype='rollup'):
        """
        Rollups which evaluate to arrays accept a filter with an any, every, or none condition; 
        rollups which evaluate to numbers accept a filter with a number condition; 
        The criterion itself can be any other property type.	
        and rollups which evaluate to dates accept a filter with a date condition.
        ---
        :param fcon any: = 'any'
        For a rollup property which evaluates to an array, 
        >>> { "any": { "rich_text": { "contains": "kale" } }
        
        :param fcon every: = 'every'
        For a rollup property which evaluates to an array, 
        >>> { "every": { "rich_text": { "contains": "kale" } }
        
        :param fcon none: = 'none'
        For a rollup property which evaluates to an array, 
        >>> { "none": { "rich_text": { "contains": "kale" } }
        
        :param fcon number: = 'number'
        >>> { "number": { "equals": 42 } }
        
        :param fcon date: = 'date'
        >>> { "date": { "equals": 42 } }
        """
        return cls(pname, ptype, fcon=fcon, fval=fval)

    #     formula
    #     """Property:
    #     string: text filter condition - Only return pages where the result type of the page 
    #             property formula is "string" and the provided string matches the formula's value.
    #     checkbox: checkbox filter condition - Only return pages where the result type of the page 
    #             property formula is "checkbox" and the provided checkbox matches the formula's value.
    #     number: number filter condition - Only return pages where the result type of the page 
    #             property formula is "number" and the provided number matches the formula's value.
    #     date: date filter condition - Only return pages where the result type of the page 
    #             property formula is "date" and the provided date matches the formula's value.
    #     Where the object would be the respective filter condition.
    #     ---
    #     https://developers.notion.com/reference/post-database-query-filter#formula-filter-condition
    #     """

    @classmethod
    def text(cls, pname: str, ptype: TextTypes, fcon: TextConditions, fval):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def checkbox(cls, pname: str, fcon: CheckboxConditions, fval, ptype='checkbox'):
        return cls(pname, ptype, fcon=fcon, fval=fval)
 
    @classmethod
    def number(cls, pname: str, fcon: NumberConditions, fval, ptype='number'):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def select(cls, pname: str, fcon: SelectConditions, fval, ptype='select'):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def multi_select(cls, pname: str, fcon: MultiSelectConditions, fval, ptype='multi_select'):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def status(cls, pname: str, fcon: StatusConditions, fval, ptype='status'):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def date(cls, pname: str, ptype: DateTypes, fcon: DateConditions, fval):
        """When selecting any DateCondition containing `past`, `this`, or `next`
        set fval to `{}`
        ---
        Using `notion.payload` will convert datetime objects to ISO format.
        """
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def people(cls, pname: str, ptype: PeopleTypes, fcon: PeopleConditions, fval):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def files(cls, pname: str, fcon: FilesConditions, fval, ptype='files'):
        return cls(pname, ptype, fcon=fcon, fval=fval)

    @classmethod
    def relation(cls, pname: str, fcon: RelationConditions, fval, ptype='relation'):
        return cls(pname, ptype, fcon=fcon, fval=fval)
