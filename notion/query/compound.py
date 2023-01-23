from typing import Sequence, Union

from notion.query.propertyfilter import PropertyFilter

__all__: Sequence[str] = (
    'CompoundFilter', 
    'CompoundAnd', 
    'CompoundOr'
)

PropertyFilters = Union[PropertyFilter, Sequence[PropertyFilter]]


class CompoundAnd:
    """See doc in module `query.compound_filter_objects` and `CompoundFilter()`"""
    def __new__(cls, *filters: PropertyFilters) -> dict[str, list[PropertyFilters]]:
        return {'and': [f for f in filters]}

class CompoundOr:
    """See doc in module `query.compound_filter_objects` and `CompoundFilter()`"""
    def __new__(cls, *filters: PropertyFilters) -> dict[str, list[PropertyFilters]]:
        return {'or': [f for f in filters]}

class CompoundFilter:
    """
    :param operator: :class:`CompoundAnd` or :class:`CompoundOr` 
                     array of PropertyFilter objects or CompoundFilter objects.
                     Returns pages when any of the filters inside the provided array match.

    Combines several filter objects together using a logical operator `and` or `or`.  
    Can also be combined within a compound filter, 
    NOTE: only up to two nesting levels deep.

    See doc in module `query.compound_filter_objects` for an example.
    
    https://developers.notion.com/reference/post-database-query-filter#compound-filter-object
    """
    def __new__(cls, *operator: CompoundOr | CompoundAnd) -> dict[str, CompoundOr | CompoundAnd]:
        return {'filter': f for f in operator}


__doc__ = \
"""
query_payload = payload(
    CompoundFilter(
        CompoundOr(
            PropertyFilter.text(
                'Description', 'email', 'contains', 'fish').compound(), 
        CompoundAnd(
            PropertyFilter.select(
                'Food group', 'equals', 'Vegetable').compound(), 
            PropertyFilter.checkbox(
                'Is protein rich?', 'equals', True).compound()
                )
            )
        )
    )


```json
{
    "filter": {
        "or": [
            {
                "property": "Description",
                "email": {
                    "contains": "fish"
                }
            },
            {
                "and": [
                    {
                        "property": "Food group",
                        "select": {
                            "equals": "Vegetable"
                        }
                    },
                    {
                        "property": "Is protein rich?",
                        "checkbox": {
                            "equals": true
                        }
                    }
                ]
            }
        ]
    }
}
```
"""
