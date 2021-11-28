from typing import Union, Text, Iterable, KeysView
from uuid import UUID

ObjectID = Union[str, UUID]
ObjectIDs = Union[Iterable[ObjectID], KeysView]
