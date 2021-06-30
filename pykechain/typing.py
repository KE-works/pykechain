from typing import Union, Text, Iterable, KeysView
from uuid import UUID

ObjectID = Union[Text, UUID]
ObjectIDs = Union[Iterable[ObjectID], KeysView]
