import os

from pykechain.exceptions import IllegalArgumentError

from pykechain.enums import Category, PropertyType
from tests.utils import temp_chdir


def move_part(part, target_parent, name=None, keep_original=True, include_children=True):
    """

    Parameters
    ----------
    part
    target_parent
    name
    keep_original
    include_children

    Returns
    -------

    """
    if not name:
        name = "CLONE - {}".format(part.name)

    if part.category == Category.MODEL and target_parent.category == Category.MODEL:
        moved_part_model = target_parent.add_model(name=name, multiplicity=part.multiplicity)
        for prop in part.properties:
            prop_type = prop._json_data['property_type']
            desc = prop._json_data['description']
            unit = prop._json_data['unit']
            if prop_type == PropertyType.SINGLE_SELECT_VALUE:
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                                           default_value=prop.value)
                moved_prop.options = prop.options
            elif prop_type == PropertyType.REFERENCES_VALUE:
                referenced_part_ids = [referenced_part.id for referenced_part in prop.value]
                moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                              default_value=referenced_part_ids)
            elif prop_type == PropertyType.ATTACHMENT_VALUE:
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type)
                if prop.value:
                    attachment_name = prop._json_data['value'].split('/')[-1]
                    with temp_chdir() as target_dir:
                        full_path = os.path.join(target_dir or os.getcwd(), attachment_name)
                        prop.save_as(filename=full_path)
                        moved_prop.upload(full_path)
            else:
                moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                              default_value=prop.value, unit=unit)

    elif part.category == Category.INSTANCE and target_parent.category == Category.INSTANCE:
        pass
    else:
        raise IllegalArgumentError('part and target_parent must be both MODELS or both INSTANCES')