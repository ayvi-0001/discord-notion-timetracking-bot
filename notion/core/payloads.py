from typing import overload, Sequence, Any
import dataclasses
import json

from pydantic.json import pydantic_encoder

from notion.core.typehints import *

__all__: Sequence[str] = ("payload", "named_property", "_asdict")


# from notion.objects.pagepropertyvalues import NotionProperty

# @overload
# def payload(*args: PropertyFilter) -> Json[str]:
#     ...

# @overload
# def payload(*args: NotionProperty[Any]) -> Json[str]:
#     ...

# @overload
# def payload(*args: dict[str, str]) -> Json[str]:
#     ...

# @overload
# def payload(*args: tuple[dict, dict]) -> Json[str]:
#     ...

def payload(*args) -> Json[str]:
    """
    Example:
    ```
    sample_db.update(
        notion.payload(
            objects.Properties(
                notion.named_property('created', notion.CreatedTimeSchema()),
                notion.named_property('last_edit', notion.LastEditedTimeSchema()),
                notion.named_property('timer', notion.FormulaSchema(expression_timer)),
                )
            )
        )
    ```
    """
    combined: dict[Any, Any] = {}
    for x in args:
        combined.update(_asdict(x)) if dataclasses.is_dataclass(x) else combined.update(x)
        # combined.update(_asdict(x)) if dataclasses.is_dataclass(x) else x
    payload = json.dumps(combined, default=pydantic_encoder, indent=4)
    return payload


def remove_nulls(obj: list | dict):
    if isinstance(obj, list):
        return [remove_nulls(x) for x in obj if x is not None]
    if isinstance(obj, dict):
        return {
            key: remove_nulls(val)
            for key, val in obj.items()
            if val is not None
        }
    else:
        return obj


def _asdict(obj) -> Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(
            obj, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
    else:
        return remove_nulls(obj)    
    

def named_property(name, dc):
    _construct = dataclasses.make_dataclass(
        f'{name}', [(f'{name}')]
        )
    _named_property = _construct(dc)
    return _asdict(_named_property)
