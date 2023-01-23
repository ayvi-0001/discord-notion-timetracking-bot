from __future__ import annotations

import typing

from notion.core import *
from notion.properties import *
from notion.api.notionblock import Block
from notion.api.notiondatabase import Database
from notion.api.base_object import _BaseNotionBlock

__all__: typing.Sequence[str] = ["Page"]


class Page(_BaseNotionBlock):
    def __init__(self, id: str, token: str | None = None, notion_version: str | None = None):
        super().__init__(id=id, token=token, notion_version=notion_version)


    @classmethod
    def create(
        cls, data: Json[str], parent_instance: typing.Union[Page, Database, Block]
    ) -> typing.Self:
        """
        Required:
        :param parent_instance: Any notion object with a valid id

        Creates a new page in the specified database or child of an 
        existing page. If the parent is a database, property values in the 
        properties parameter of the new page must conform to the parent 
        database's property schema. If the parent is a page, the only 
        valid property is title. The new page may include page content,
        described as blocks in the children parameter.

        Current version of the api does not allow pages to be created
        to the parent `workspace`

        https://developers.notion.com/reference/post-page 
        """
        # TODO add data payload
        _id = parent_instance.id
        url = Page(_id)._endpoint('pages', object_id=None)

        new_page = Page(_id)._post(url=url, data=data)
        if new_page['object'] == 'error':
            logging.info(f"{new_page['message']}")

        new_page_id = new_page.get('id')

        logging.info(f"created a new page in {parent_instance.__repr__()} | ")
        logging.info(f"new page id = {new_page_id}".replace('-',''))

        return cls(id=new_page_id)


    @classmethod
    def blank(
        cls, parent_instance: typing.Union[Page, Database, Block], 
        content: typing.Optional[str | typing.Any] = None, 
        icon_url: typing.Optional[str] = None, 
        link: typing.Optional[str] = None
    ) -> typing.Self:
        """
        Required:
        :param parent_instance: Any notion object with a valid id
        :param content: title of page

        Optional
        :param link: hyperlink in page title text
        :param icon_url: external link to icon image, see external files in notion.objects.common

        Creates a blank page in either a parent Page or Database. 
        Combine with Blocks.append() to include content, 
        or use Database.create() to manage page properties.
        """
        if parent_instance.type == 'child_database':
            parent = Parent.database(parent_instance.id)
        else:
            parent = Parent.page(parent_instance.id)
        
        payload = (_asdict(parent) | 
                   named_property('properties', Title(content, link))
                   )
        if icon_url:
            payload = payload | _asdict(Icon.external(icon_url))

        _id = parent_instance.id
        url = Page(_id)._endpoint('pages', object_id=None)

        new_page = Page(_id)._post(url=url, data=payload)
        if new_page['object'] == 'error':
            logging.info(f"{new_page['message']}")

        new_page_id = new_page.get('id')

        logging.info(f"created a new page in {parent_instance.__repr__()} | ")
        logging.info(f"new page id = {new_page_id}".replace('-',''))

        return cls(id=new_page_id)

    def retrieve(self, data: Json[str | None] = None) -> typing.Any:
        """Retrieves a Page object using the ID specified. 
        https://developers.notion.com/reference/retrieve-a-page 
        """
        url = super()._endpoint('pages', 
                                object_id=self.id)
        return super()._get(url=url, data=data)

    def property_names(self) -> list[str]:
        """Returns property names by default. Set 'ids' to true to return
        Property ids. Response references schema of the parent database.
        """
        if self.parent_type == 'workspace' or self.parent_type == 'id':
            raise ValueError('Only pages in a database will have property ids')
        else:
            return Database(self.parent_id).property_names()

    def retrieve_property_item(self, property_id, data=None, cursor: bool = False) -> typing.Any:
        """Retrieves a property_item object for a given page_id and 
        property_id. The object returned will either be a value or 
        a paginated list of property item values.
        To obtain property_id's, use the Retrieve a database endpoint. 
        https://developers.notion.com/reference/retrieve-a-page-property 
        """
        url = super()._endpoint('pages', 
                                properties=True, 
                                property_id=property_id, 
                                object_id=self.id)
        if cursor is True:
            return super()._get(url=url, data=data, cursor=True)
        else:
            return super()._get(url=url, data=data)

    def patch_properties(self, data=None) -> typing.Any:
        """Updates page property values for the specified page. Properties
        that are not set via the properties parameter will remain unchanged.
        If the parent is a database, the new property values in the properties 
        parameter must conform to the parent database's property schema. 
        https://developers.notion.com/reference/patch-page 
        """
        # LIMITATIONS: Updating rollup property values is not supported.
        url = super()._endpoint('pages', object_id=self.id)
        return super()._patch(url=url, data=data)

    def update_checkbox(self, prop_name: str, prop_value: bool) -> typing.Any:
        """
        Errors:
        raises value error if property does not exist.

        Updates the checkbox page property value defined in the parent
        database schema.
        """
        checkbox = named_property(prop_name, CheckBoxPropertyValue(checkbox=prop_value))
        payload = named_property('properties', checkbox)

        url = super()._endpoint('pages', object_id=self.id)
        response = super()._patch(url, data=payload)
        if response['object'] == 'error':
            raise ValueError(f"{response['message']}")
        return response
