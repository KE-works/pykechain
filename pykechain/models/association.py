from typing import Optional

import requests

from pykechain.enums import Category
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import BaseInScope
from pykechain.models.input_checks import check_base, check_type
from pykechain.models.widgets import Widget


class Association(BaseInScope):
    """
    A virtual object representing a KE-chain association.

    :ivar property_instance_id
    :ivar property_model_id
    :ivar part_instance_id
    :ivar part_model_id
    :ivar widget_id
    :ivar activity_id
    :ivar writable
    """

    def __init__(self, json, client):
        """Construct an association from provided json data."""
        super().__init__(json=json, client=client)

        self.property_instance_id = json.get('instance_property')
        self.property_model_id = json.get('model_property')
        self.part_instance_id = json.get('instance_part')
        self.part_model_id = json.get('model_part')
        self.widget_id = json.get('widget')
        self.activity_id = json.get('activity')
        self.writable = json.get('writable')
        self.permissions = json.get('permissions')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} id {}>".format(self.__class__.__name__, self.id)

    @property
    def is_model(self) -> bool:
        """
        Specify whether the association relates a Part model (true) or Part instance (false).

        :return: boolean
        :rtype bool
        """
        return self.part_instance_id is None

    def edit(
            self,
            widget: Optional[Widget] = None,
            property: Optional['Property'] = None,
            writable: Optional[bool] = None,
            **kwargs
    ) -> None:
        """
        Update the attributes of this association.

        :param widget: A Widget object or its uuid
        :param property: A Property object or its uuid
        :param writable: (optional) boolean to specify whether the property can be edited (True) or is read-only (False)
        :return: None
        """
        check_base(widget, Widget, 'widget')
        from pykechain.models import Property
        check_base(property, Property, 'property')
        check_type(writable, bool, 'writable')

        if widget.scope_id != property.scope_id:
            raise IllegalArgumentError("`widget` and `property` must belong to the same scope.")

        update_dict = {
            "activity": widget._activity_id,
            "widget": widget.id,
            "scope": widget.scope_id,
            "writable": writable,
        }

        if property.category == Category.INSTANCE:
            update_dict.update({
                "instance_property": property.id,
                "instance_part": property.part_id,
            })
            property_model = property.model()
        else:
            property_model = property

        update_dict.update({
            "model_property": property_model.id,
            "model_part": property_model.part_id,
        })

        if kwargs:
            update_dict.update(kwargs)

        url = self._client._build_url('association', association_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Association {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

    def delete(self) -> None:
        """
        Delete the association.

        :return: None
        """
        self._client.delete_association(association=self)
