import typing

from dataclasses import InitVar
from dataclasses import is_dataclass

from pydantic import Field
from pydantic.dataclasses import dataclass

from notion.core.payloads import _asdict
from notion.core.payloads import named_property

__all__: typing.Sequence[str] = (
    "Parent",
    "Properties",
    "FilesObject",
    "_InternalFile",
    "_ExternalFile",
    "Cursor",
    "Children",
    "Icon",
)


@dataclass(kw_only=False)
class Parent:
    """ 
    Required:
    :param id: uuid of parent page/database/block
    ---
    Parenting rules:
    Pages can be parented by other pages, databases, blocks, or by the whole workspace.
    Blocks can be parented by pages, databases, or blocks.
    Databases can be parented by pages, blocks, or by the whole workspace.
    https://developers.notion.com/reference/parent-object
    ```json
    {
        "parent": {
            "type": "page_id",
            "page_id": "59833787-2cf9-4fdf-8782-e53db20768a5"
        }
    }
    ```
    """
    id: InitVar[str]
    parent: dict = Field(default_factory=dict)

    @classmethod
    def page(cls, id, type='page_id'):
        return cls(id=id, parent={'type':type} | {type:id})
    
    @classmethod
    def database(cls, id, type='database_id'):
        return cls(id=id, parent={'type':type} | {type:id})
    
    @classmethod
    def block(cls, id, type='block_id'):
        return cls(id=id, parent={'type':type} | {type:id})


class Properties:
    def __new__(cls, *args):
        combined = {}
        for x in args:
            combined.update(_asdict(x)) if is_dataclass(x) else combined.update(x)
        properties = named_property('properties', combined)
        return properties


@dataclass(kw_only=False)
class _InternalFile:
    type: str = 'file'
    name: str | None = None
    url: InitVar[str | None] = None
    file: dict = Field(default_factory=dict)
    
    def __post_init__(self, url):
        self.file = {"url": url}


@dataclass(kw_only=False)
class _ExternalFile: 
    name: str | None = None
    type: str = 'external'
    url: InitVar[str | None] = None
    external: dict = Field(default_factory=dict)

    def __post_init__(self, url):
        self.external = {"url": url}


@dataclass(kw_only=False)
class FilesObject:
    """
    Required:
    :param name: file name.
    :param url: link to either an interal/external file.
    Must use either classmethod (internal/external)
    ---
    An array of file objects.
    NOTE: Updating a file property overwrites the value by the array of files passed.
    Although Notion doesn't support uploading files, if you pass a file object containing 
    a file hosted by Notion, it remains one of the files. 
    To remove any file, just don't pass it in the update response.
    https://developers.notion.com/reference/page-property-values#files 
    ```json
    {
        "type": "files",
        "files": [
            {
                "name": "filename",
                "type": "external",
                "external": {
                    "url": "someurl@url.com"
                }
            }
        ]
    }
    ```
    """
    url: InitVar[str | None] = None
    name: InitVar[str | None] = None
    type: str | None = None
    files: list[_InternalFile | _ExternalFile] = Field(default_factory=list)

    def __repr__(self, name: set[str] | None = None, url: set[str] | None = None):
        return f'FilesObject(name={name},url={url})'

    def __post_init__(self, name, url):
        if self.type is None:
            raise TypeError(
                f'{self.__repr__({name}, {url})} was not called by a classmethod'
                )

    @classmethod
    def internal(cls, url, name):
        _file = _InternalFile(name=name, url=url)
        return cls(type='files', files=[_file])
    
    @classmethod
    def external(cls, url, name):
        _file = _ExternalFile(name=name, url=url)
        return cls(type='files', files=[_file])


@dataclass(kw_only=False)
class Icon:
    icon: dict = Field(default_factory=dict)
    url: InitVar[str | None] = None

    @classmethod
    def external(cls, url: str | None = None, type='external'):
        _external = {type:{'url':url}}
        return cls(url=url, icon=({'type':type} | _external))


@dataclass(kw_only=False)
class Cursor:
    next_cursor: str


@dataclass(kw_only=False)
class Children:
    children: list = Field(default_factory=list)

