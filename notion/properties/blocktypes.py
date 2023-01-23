# from typing import Sequence

# from dataclasses import InitVar
# from pydantic.dataclasses import dataclass


# @dataclass(kw_only=False)
# class ParagraphBlock: 
#     type: str = 'paragraph'

# @dataclass(kw_only=False)
# class HeadingOneBlock: 
#     type: str = 'heading_1'

# @dataclass(kw_only=False)
# class HeadingTwoBlock: 
#     type: str = 'heading_2'

# @dataclass(kw_only=False)
# class HeadingThreeBlock: 
#     type: str = 'heading_3'

# @dataclass(kw_only=False)
# class CalloutBlock: 
#     type: str = 'callout'

# @dataclass(kw_only=False)
# class QuoteBlock: 
#     type: str = 'quote'

# @dataclass(kw_only=False)
# class BulletedListItemBlock: 
#     type: str = 'bulleted_list_item'

# @dataclass(kw_only=False)
# class NumberedListItemBlock: 
#     type: str = 'numbered_list_item'

# @dataclass(kw_only=False)
# class ToDoBlock: 
#     type: str = 'to_do'

# @dataclass(kw_only=False)
# class ToggleBlock: 
#     type: str = 'toggle'

# @dataclass(kw_only=False)
# class CodeBlock: 
#     type: str = 'code'

# @dataclass(kw_only=False)
# class ChildPageBlock: 
#     type: str = 'child_page'

# @dataclass(kw_only=False)
# class ChildDatabaseBlock: 
#     type: str = 'child_database'

# @dataclass(kw_only=False)
# class EmbedBlock: 
#     type: str = 'embed'

# @dataclass(kw_only=False)
# class ImageBlock: 
#     type: str = 'image'

# @dataclass(kw_only=False)
# class VideoBlock: 
#     type: str = 'video'

# @dataclass(kw_only=False)
# class FileBlock: 
#     type: str = 'file'

# @dataclass(kw_only=False)
# class PdfBlock: 
#     type: str = 'pdf'

# @dataclass(kw_only=False)
# class BookmarkBlock: 
#     type: str = 'bookmark'

# @dataclass(kw_only=False)
# class EquationBlock: 
#     type: str = 'equation'

# @dataclass(kw_only=False)
# class TableOfContentsBlock: 
#     type: str = 'table_of_contents'

# @dataclass(kw_only=False)
# class ColumnListBlock: 
#     type: str = 'column_list'

# @dataclass(kw_only=False)
# class ColumnBlock: 
#     type: str = 'column'

# @dataclass(kw_only=False)
# class LinkPreviewBlock: 
#     type: str = 'link_preview'

# @dataclass(kw_only=False)
# class TemplateBlock: 
#     type: str = 'template'

# @dataclass(kw_only=False)
# class LinkToPageBlock: 
#     type: str = 'link_to_page'

# @dataclass(kw_only=False)
# class SyncedBlockBlock: 
#     type: str = 'synced_block'

# @dataclass(kw_only=False)
# class TableBlock: 
#     type: str = 'table'

# @dataclass(kw_only=False)
# class TableRowBlock: 
#     type: str = 'table_row'

# @dataclass(kw_only=False)
# class DividerBlock: ...
# @dataclass(kw_only=False)
# class BreadcrumbBlock: ...
