from pykechain.models import BaseInScope


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
