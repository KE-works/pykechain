from pykechain.models import Base


class Association(Base):
    """
    A virtual object representing a KE-chain association.

    :ivar property_instance_id
    :ivar property_model_id
    :ivar part_instance_id
    :ivar part_model_id
    :ivar widget_id
    :ivar activity_id
    :ivar scope_id
    :ivar writable
    """
    def __init__(self, json, client, **kwargs):
        super().__init__(json=json, client=client)

        self.property_instance_id = json.get('instance_property')
        self.property_model_id = json.get('model_property')
        self.part_instance_id = json.get('instance_part')
        self.part_model_id = json.get('model_part')
        self.widget_id = json.get('widget')
        self.activity_id = json.get('activity')
        self.scope_id = json.get('scope')

        self.writable = json.get('writable')
        self.permissions = json.get('permissions')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} id {}>".format(self.__class__.__name__, self.id)
