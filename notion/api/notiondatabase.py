from __future__ import annotations

import typing
from functools import cached_property

from notion.core import *
from notion.properties import *
from notion.api.base_object import _BaseNotionBlock

__all__: typing.Sequence[str] = ['Database']


class Database(_BaseNotionBlock):
    def __new__(cls, id: str, token: str | None = None, notion_version: str | None = None):
        _block = _BaseNotionBlock(id)
        if _block.type != 'child_database':
            raise ValueError(
                f"<{__class__.__name__}('{id}')> does not reference a Database")
        else: 
            return super().__new__(cls)


    @classmethod
    def create(cls, data: Json[str], parent_instance) -> typing.Self:
        """
        Minimum objects required in payload:
        :parent object, and properities with a title object:

        Creates a non-inline database in the specified parent page, 
        with the specified properties schema.
        Currently, Databases cannot be created to the parent workspace.
        https://developers.notion.com/reference/post-page 
        """
        # TODO Is not using the parent id as a target location yet,
        # still relying on id in the payload.
        if parent_instance.type == 'child_database':
            raise ValueError('Cannot create a database in a database')

        url = Database(parent_instance.id)._endpoint('databases')
        new_db = Database(parent_instance.id)._post(url, data=data)
        if new_db['object'] == 'error':
            logging.info(f"{new_db['message']}")
        new_db_id = new_db.get('id')

        return cls(id=new_db_id)

    @cached_property
    def retrieve(self) -> typing.Any:
        """Retrieves a Database object using the ID specified. 
        https://developers.notion.com/reference/retrieve-a-database
        """
        url =super()._endpoint('databases', object_id=self.id)
        return super()._get(url)
    
    @cached_property
    def property_schema(self) -> dict[str, str]:
        response = self.retrieve['properties']
        return response

    @property
    def property_names(self) -> typing.Any:
        return [key for key in self.retrieve.get('properties').keys()]

    def update(self, data=None) -> typing.Any:
        """Updates an existing database as specified by the parameters.
        https://developers.notion.com/reference/update-a-database
        """
        url = super()._endpoint('databases', object_id=self.id)
        response = super()._patch(url, data=data)
        if response['object'] == 'error':
            logging.info(f"{response['message']}")
        else:
            logging.info(f'<{self.__repr__()}> updated \n`{data}`')
        return response

    def delete_property(self, name_or_id: str) -> None:
        """Delete a property by either the property name or id. 
        This can be found in the schema with Database.retrieve() 
        """
        payload = {'properties':{name_or_id:None}}
        logging.info(f'<{self.__repr__()}> deleted property `{name_or_id}`')
        self.update(data=payload)
    
    def rename_property(self, old_name: str, new_name: str) -> None:
        """ Rename a property by either the property name or id. 
        This can be found in the schema with Database.retrieve() 
        """
        payload = {'properties':{old_name:{'name':new_name}}}
        logging.info(f'<{self.__repr__()}> renamed property `{old_name}` to {new_name}')
        self.update(data=payload)

    def query(self, data = None, cursor: bool = False) -> typing.Any:
        """Gets a list of Pages contained in the database, filtered/ordered 
        to the filter conditions/sort criteria provided in request. 
        The response may contain fewer than page_size of results. 
        Responses from paginated endpoints contain a `next_cursor` property, 
        which can be used in a query payload to continue the list.
        https://developers.notion.com/reference/update-a-database 

        NOTE: page_size Default: 100 page_size Maximum: 100.

        If cursor is set to True, will return a tuple with the 
        first value containing the response, and the second value containing
        a dict of the next_cursor. 
        E.g.
        >>> {'next_cursor': 'f88aaecb-f6e1-4269-93d4-feafd450172e'} 
        """
        url = super()._endpoint('databases', 
                                query=True, 
                                object_id=self.id)
        if cursor is True:
            return super()._post(url=url, data=data, cursor=True)
        else:
            return super()._post(url=url, data=data)
