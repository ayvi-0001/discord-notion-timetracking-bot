from __future__ import annotations

import typing

from notion.core import *
from notion.properties import *
from notion.api.base_object import _BaseNotionBlock

__all__: typing.Sequence[str] = ["Block"]


class Block(_BaseNotionBlock):
    """These are the individual 'nodes' in a page that you typically 
    interact with in Notion. 
    """
    def __init__(self, id: str, token: str | None = None, notion_version: str | None = None):
        super().__init__(id=id, token=token, notion_version=notion_version)

    def retrieve(self) -> typing.Any:
        """Retrieves a Block object using the ID specified. 
        https://developers.notion.com/reference/retrieve-a-block 
        """
        url = super()._endpoint('blocks', object_id=self.id)
        return super()._get(url)
    
    def retrievechildren(self, cursor: bool = False) -> typing.Any:
        """Returns a paginated array of child block objects contained 
        in the block using the ID specified. 
        In order to receive a complete representation of a block, you 
        may need to recursively retrieve block children of child blocks
        https://developers.notion.com/reference/get-block-children

        page_size Default: 100 page_size Maximum: 100.
        If cursor is set to True, will return a tuple with the 
        first value containing the response, 
        and the second value containing a dict of the next_cursor
        """
        url = super()._endpoint('blocks', children=True, object_id=self.id)
        if cursor is True:
            return super()._get(url, cursor=True)
        else:
            return super()._get(url)

    def append_block(self, data: Json[str]) -> typing.Any:
        """Creates/appends new children blocks to the parent 
        block_id specified. Returns a paginated list of newly created 
        children block objects. BODY PARAMS: children | Child 
        content to append to a container block as an array of 
        block objects
        https://developers.notion.com/reference/patch-block-children 
        """
        url = super()._endpoint('blocks', children=True, object_id=self.id)
        return super()._patch(url, data)

    def delete_self(self) -> None:
        """Sets a Block object, including page blocks, to archived: true 
        using the ID specified. Note: in the Notion UI application, 
        this moves the block to the "Trash" where it can still be 
        accessed and restored. To restore the block with the API, 
        use the Update a block or Update page respectively. 
        https://developers.notion.com/reference/delete-a-block
        To delete a page/database, create as a block instance and call method.
        """
        url = super()._endpoint('blocks', object_id=self.id)
        return super()._delete(url)
    
    def restore_self(self) -> None:
        """Sets "archived" key to false. 
        Only works if the parent page has not been deleted from the trash.
        """
        url = super()._endpoint('blocks', object_id=self.id)
        return super()._patch(url, data=(b'{"archived": false}'))

    def delete_child(self, children_id: list) -> None:
        for id_ in children_id:
            url = super()._endpoint('blocks', object_id=id_)
            super()._delete(url)

            logging.info(f"<{self.__repr__()}> deleted child block {id_}")
    
    def restore_child(self, children_id) -> None:
        for id_ in children_id:
            url = super()._endpoint('blocks', object_id=id_)
            super()._patch(url, data=(b'{"archived": false}'))

            logging.info(f"<{self.__repr__()}> restored child block {id_}")

    def update(self, data: Json[str]) -> typing.Any:
        """Updates content for the specified block_id based on the block 
        type. Supported fields based on the block object type. 
        Note: The update replaces the entire value for a given field. 
        If a field is omitted (ex: omitting checked when updating a 
        to_do block), the value will not be changed. 
        https://api.notion.com/v1/blocks/{block_id} 
        """
        url = super()._endpoint('blocks', object_id=self.id)
        return super()._patch(url, data=data)       

    # To update title of a child_page block, use the pages endpoint
    # To update title of a child_database block, use the databases endpoint
    # To update toggle of a heading block, you can include the optional is_toggleable property in the request 
    # Toggle can be added and removed from a heading block. However, 
    # you cannot remove toggle from a heading block if it has children
    # All children MUST be removed before revoking toggle from a heading block
