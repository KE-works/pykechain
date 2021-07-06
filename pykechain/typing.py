from typing import Iterable, KeysView, Union
from uuid import UUID

ObjectID = Union[str, UUID]
ObjectIDs = Union[Iterable[ObjectID], KeysView]
