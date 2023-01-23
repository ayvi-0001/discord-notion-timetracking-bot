"""Rich text objects contain the data that Notion uses to display 
formatted text, mentions, and inline equations. 
Arrays of rich text objects within database property objects and 
page property value objects are used to create what a user 
experiences as a single text value in Notion. 
https://developers.notion.com/reference/rich-text
"""

import typing

from dataclasses import InitVar
from pydantic import Field
from pydantic.dataclasses import dataclass

from notion.core.payloads import _asdict
from notion.properties.options import ColorEnum


__all__: typing.Sequence = (
    "Annotations",
    "RichEquation",
    "RichText",
    "TemplateMention",
    "PageMention",
    "DatabaseMention",
    "LinkPreviewMention",
    "DateMention",
    "UserObject",
    "UserMention",
    "RichMention",
    "Title",
)



@dataclass(kw_only=False) 
class Annotations:
    annotations: typing.Sequence[str] | typing.Any = Field(default_factory=dict)
    bold: InitVar[bool | None] = None
    italic: InitVar[bool | None] = None
    strike: InitVar[bool | None] = None
    underline: InitVar[bool | None] = None
    code: InitVar[bool | None] = None
    color: InitVar[ColorEnum | None] = None

    def __post_init__(self, bold, italic, strike, underline, code, color):
        if any([bold, italic, strike, underline, code, color]):
            self.annotations = (
                {'bold': bold}
                | {'italic': italic}
                | {'strike': strike}
                | {'underline': underline}
                | {'code': code}
                | {'color': color}
              )
        else: 
            self.annotations = None


@dataclass(kw_only=False) 
class RichEquation:
    """
    Required:
    :param expression: LaTeX string representing inline equation
    Optional:
    :param annotations: Annotations Object
    :param href: Hyperlink
    ---
    https://developers.notion.com/reference/rich-text#rich-text-type-objects
    """
    expression: InitVar[typing.Any]
    input_annotations: InitVar[Annotations | None] = None
    type: str = Field(default='equation')
    equation: dict = Field(default_factory=dict)
    annotations: Annotations | None = None
    href: str | None = None

    def __post_init__(self, expression, input_annotations):
        self.equation = {'equation': expression}
        self.annotations = input_annotations


@dataclass(kw_only=False) 
class RichText:
    r"""
    Optional:
    :param content: text content in block
    :param link: hyperlink in text
    :param annotations: Annotations Object
    :param href: Hyperlink
    ---
    Using `shift+enter` for multi-line text blocks results in 
    a separate `text` key with a newline escape. E.g.

    ```json
    },  // ... first text line above
    {
        "type": "text",
        "text": {
            "content": "\ntest multi line break"
        }
    }   
    ```
    ---
    adding a link to only part of a string will split them up and return
    as separate keys in the rich text object.
    
    hyperlinking text to an internal Notion link will populate link/href
    with the UUID's following notion.so/{workspace name}/...

    ```json
    {
        "type": "text",
        "text": {
            "content": "hyperlink in text to notion link\n",
            "link": {
                "url": "/3a2ec1e9308b4fd5a5749a5ee5aeeff9?v=f19121cb8e6f4329aba62edef93c39dc&p=bc5d3abdf3a942e0b6a7d8a5c94b5dc9&pm=s"
            }          // database id // database view id // database page id
    },

    ```
    ---
    https://developers.notion.com/reference/rich-text
    """
    content: InitVar[typing.Any] = None
    link: InitVar[typing.Any] = None
    input_annotations: InitVar[Annotations | None] = None
    type: str = Field(default='text')
    text: dict | None = None
    annotations: Annotations | None = None
    href: str | None = None
    
    def __post_init__(self, content, link, input_annotations):
        self.text = ({'content': content} | {'link':link})
        self.annotations = input_annotations
    

@dataclass(kw_only=False) 
class TemplateMention:
    """Templates can include placeholder date and user mentions that populate 
    when a template is duplicated. Template mentions refer to these values.
    ---
    
    Template mention rich text objects contain a template_mention object 
    with a nested type key that is either "template_mention_date" or "template_mention_user".
    
    `template_mention_date` : The type of the date mention. 
    Possible values include: `today` and `now`.

    `template_mention_user`: The type of the user mention. 
    The only possible value is "me".
    ```json
    {
        "type": "template_mention",
        "template_mention": {
            "type": "template_mention_date",
            "template_mention_date": "today"
        }
    }
    ```
    ---
    https://developers.notion.com/reference/rich-text#template-mention-type-object
    """
    mtype: InitVar[typing.Any]
    mtype_var: InitVar[typing.Any]
    type: str = Field(default='template_mention')
    template_mention: dict = Field(default_factory=dict)

    def __post_init__(self, mtype, mtype_var):
        self.template_mention = {"type": mtype} | {mtype: mtype_var}

    @classmethod
    def today(cls, _mtype="template_mention_date", mtype_var: str='today'):
        return cls(mtype=_mtype, mtype_var=mtype_var)
    
    @classmethod
    def now(cls, _mtype="template_mention_date", mtype_var: str='now'):
        return cls(mtype=_mtype, mtype_var=mtype_var)

    @classmethod
    def me(cls, _mtype="template_mention_user", mtype_var: str='me'):
        return cls(mtype=_mtype, mtype_var=mtype_var)


@dataclass(kw_only=False) 
class PageMention:
    page_id: InitVar[typing.Any]
    type: str = Field(default='page')
    page: dict = Field(default_factory=dict)

    def __post_init__(self, page_id):
        self.page = {'id':page_id}


@dataclass(kw_only=False) 
class DatabaseMention:
    database_id: InitVar[typing.Any]
    type: str = Field(default='database')
    database: dict = Field(default_factory=dict)

    def __post_init__(self, database_id):
        self.database = {'id':database_id}


@dataclass(kw_only=False) 
class LinkPreviewMention:
    link_preview_url: InitVar[typing.Any]
    type: str = Field(default='link_preview')
    link_preview: dict = Field(default_factory=dict)

    def __post_init__(self, link_preview_url):
        self.link_preview = {'url':link_preview_url}


@dataclass(kw_only=False) 
class DateMention:
    """ 
    Required:
    :param start : If the "date" value is a range, then represents start of the range.
    Optional:
    :param end: A string representing the end of a date range. 
                If the value is null, then the date value is not a range.
    https://developers.notion.com/reference/rich-text#date-mention-type-object 
    """
    start: InitVar[typing.Any]
    end: InitVar[typing.Any]
    type: str = Field(default='date')
    date: dict = Field(default_factory=dict)

    def __post_init__(self, start, end):
        self.date = {'start':start} | {'end':end}


@dataclass(kw_only=False)
class UserObject:
    """
    Required:
    :param name:
    :param person_email:
    ---
    The User object represents a user in a Notion workspace. 
    Users include full workspace members, and integrations. 
    Guests are not included.
    https://developers.notion.com/reference/user

    ```json
    {
        "type": "person",
        "object": "user",
        "name": "yourname",
        "person": {
            "email": "useremail@any.com"
        }
    }    
    ```
    """
    person_email: InitVar[typing.Any] = None
    name: str | None = None
    # avatar_url: TODO: not yet implemented
    type: str = Field(default='person')
    object: str = Field(default='user')
    person: dict = Field(default_factory=dict)

    def __post_init__(self, person_email):
        self.person = {'email':person_email}
   

@dataclass(kw_only=False) 
class UserMention:
    """
    Required:
    :param mention: UserObject
    ---
    If your integration doesn't yet have access to the mentioned user, 
    then the plain_text that would include a user's name reads as "@Anonymous"
    https://developers.notion.com/reference/rich-text#user-mention-type-object
    """
    type: str = Field(default='user')
    mention: UserObject | None = None


@dataclass(kw_only=False) 
class RichMention:
    """
    Mention objects represent an inline mention of a database, 
    date, link preview mention, page, template mention, or user. 
    A mention is created in the Notion UI when a user types @ 
    followed by the name of the reference.
    https://developers.notion.com/reference/rich-text#mention
    """
    type: str = Field(default='mention')
    mention: (
        DateMention
        | LinkPreviewMention 
        | DatabaseMention 
        | PageMention 
        | TemplateMention 
        | None) = None


@dataclass(kw_only=False)
class Title:
    content: InitVar[typing.Any] = None
    link: InitVar[typing.Any] = None
    title: dict = Field(default_factory=dict)

    def __post_init__(self, content, link):
        # RichText annotations not necessary for Page/Database titles.
        # _asdict removes nulls, otherwise Title throws error when creating pages
        self.title = ({'type':'title'} 
                    | {'title':[_asdict(RichText(content=content, link=link))]}
                )
