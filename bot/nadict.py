from __future__ import annotations

from typing import Any
from typing import Optional
from typing import Generator
from typing import Generator
from typing import Mapping
from typing import Sequence

__all__: Sequence[str] = ["NAdict"]


class NAdict(dict):
    """
    Returns a flatten dictionary that can access keys through attributes.
    Keys are transformed to lowercase and all non-alphanumeric characters are
    replaced with `_`.

    If the key is inside an array, then it'll be appended by the index,
    followed by the key in the array\n
    For example, to get the key `content` below
    ```json
    {
        "job_id": {
            "id": "WmTI",
            "type": "rich_text",
            "rich_text": [
                {
                    "type": "text_one",
                    "text": {
                        "content": "f8578a965c5b43a2ad4534cb6eb6cd09",
                        "link": null
                    }, //...
    ```
    ```py
    NAdict(json_object).job_id.rich_text_0_text.content

    # the key `job_id_rich_text_0_text_content` also exists,
    # but you can choose to still access through multiple attributes for better readability.
    # Or you can choose to subscript as a normal dictionary.
    ```
    """

    def __init__(self, map: Mapping[str, Any], *, sep: Optional[str] = None) -> None:
        super(NAdict, self).__init__()

        for k, v in NAdict.fdict(map, sep=sep if sep else "_").items():
            self.__setitem__(k, v)

    def __setitem__(self, k, v) -> None:
        if isinstance(v, dict):
            v = NAdict(v)
        super(NAdict, self).__setitem__(k, v)
        self.__dict__[k] = v

    def __getattr__(self, item: str) -> NAdict:
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    __setattr__ = __setitem__

    @staticmethod
    def _fdict_gen(
        d: Mapping[str, Any], parent_key: str, sep: str
    ) -> Generator[tuple[str, Any], tuple[str, dict[str, Any]], None]:
        for k, v in d.items():
            k = "".join([c if c.isalnum() else "_" for c in k]).lower()
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                yield from NAdict.fdict(v, new_key, sep=sep).items()
            if isinstance(v, list):
                try:
                    for x in enumerate(v):
                        yield from NAdict.fdict(
                            v[x[0]], f"{new_key}_{x[0]}", sep=sep
                        ).items()
                except IndexError:
                    pass
            else:
                yield new_key, v

    @staticmethod
    def fdict(
        d: Mapping[str, Any], parent_key: str = "", sep: str = "_"
    ) -> dict[str, Any]:
        return dict(NAdict._fdict_gen(d, parent_key, sep))
