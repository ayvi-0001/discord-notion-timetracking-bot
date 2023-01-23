from datetime import tzinfo
from typing import(
    Annotated,
    Sequence,
    TypeVar,
    TypeAlias,
    TypeVar,
    Protocol,
    Literal,
    Union,
)

__all__: Sequence[str] = (
    "Json", 
    "DataClass", 
    "pytz_timezone",
    "notion_endpoints",
    )

T = TypeVar("T")
Json = Annotated[T, ...]

pytz_timezone: TypeAlias = tzinfo

class DataCls(Protocol):
    __dataclass_fields__: dict[str, str]

DataClass = TypeVar("DataClass", bound=DataCls)

notion_endpoints = Literal['blocks', 'databases', 'pages']

# class NotionProperty(Protocol):
#     @abstractmethod
#     def __post_init__(self) -> dict:
#         ...

# NOTIONPROPERTY = TypeVar("NOTIONPROPERTY", bound=NotionProperty[Any])
