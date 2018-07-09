import os

from pykechain.exceptions import IllegalArgumentError

from pykechain.enums import Category, PropertyType, Multiplicity
from tests.utils import temp_chdir


# global variable
__mapping_dictionary = dict()
__edited_one_many = list()


def move_part(part, target_parent, name=None, include_children=True):
    """

    Parameters
    ----------
    part
    target_parent
    name
    include_children

    Returns
    -------

    """
    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = "CLONE - {}".format(part.name)
    # First case: Add a model to another model
    if part.category == Category.MODEL and target_parent.category == Category.MODEL:
        # The description cannot be added when creating a model, so edit the model after creation.
        part_desc = part._json_data['description']
        moved_part_model = target_parent.add_model(name=name, multiplicity=part.multiplicity)
        if part_desc:
            moved_part_model.edit(description=part_desc)

        # Map the current part model id with newly created part model Object
        __mapping_dictionary[part.id] = moved_part_model

        # TODO () Include the validators
        # Loop through properties and retrieve their type, description and unit
        for prop in part.properties:
            prop_type = prop._json_data['property_type']
            desc = prop._json_data['description']
            unit = prop._json_data['unit']

            # On "Single select" properties, options also need to be added, if they exist
            if prop_type == PropertyType.SINGLE_SELECT_VALUE:
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                                           default_value=prop.value)
                if prop.options:
                    moved_prop.options = prop.options

            # On "Part references" properties, the models referenced also need to be added
            elif prop_type == PropertyType.REFERENCES_VALUE:
                referenced_part_ids = [referenced_part.id for referenced_part in prop.value]
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                                           default_value=referenced_part_ids)

            # On "Attachment" properties, attachments needs to be downloaded and re-uploaded to the new property.
            elif prop_type == PropertyType.ATTACHMENT_VALUE:
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type)
                if prop.value:
                    attachment_name = prop._json_data['value'].split('/')[-1]
                    with temp_chdir() as target_dir:
                        full_path = os.path.join(target_dir or os.getcwd(), attachment_name)
                        prop.save_as(filename=full_path)
                        moved_prop.upload(full_path)

            # Other properties are quite straightforward
            else:
                moved_prop = moved_part_model.add_property(name=prop.name, description=desc, property_type=prop_type,
                                                           default_value=prop.value, unit=unit)

            # Map the current property model id with newly created property model Object
            __mapping_dictionary[prop.id] = moved_prop

        # Now copy the sub-tree of the part
        if include_children:
            # Populate the part so multiple children retrieval is not needed
            part.populate_descendants()
            # For each part, recursively run this function
            for sub_part in part._cached_children:
                move_part(part=sub_part, target_parent=moved_part_model, name=sub_part.name,
                          include_children=include_children)

    elif part.category == Category.INSTANCE and target_parent.category == Category.INSTANCE:
        part_model = part.model()
        target_parent_model = target_parent.model()
        move_part(part=part_model, target_parent=target_parent_model, name=part_model.name,
                  include_children=include_children)

        part.populate_descendants()
        move_part_instance(part_instance=part, target_parent=target_parent, part_model=part_model, name=name,
                           include_children=include_children)

    else:
        raise IllegalArgumentError('part and target_parent must be both MODELS or both INSTANCES')


def move_part_instance(part_instance, target_parent, part_model, name=None, include_children=True):
    """

    Parameters
    ----------
    part_instance
    target_parent
    name
    include_children

    Returns
    -------

    """
    if not name:
        name = "CLONE - {}".format(part_instance.name)
    moved_model = __mapping_dictionary[part_model.id]

    if moved_model.multiplicity == Multiplicity.ONE:
        moved_instance = moved_model.instance()
        map_property_instances(part_instance, moved_instance)
        update_part_with_properties(part_instance, moved_instance, name=name)
    elif moved_model.multiplicity == Multiplicity.ONE_MANY:
        if moved_model.id not in __edited_one_many:
            moved_instance = moved_model.instance()
            map_property_instances(part_instance, moved_instance)
            update_part_with_properties(part_instance, moved_instance, name=name)
            __edited_one_many.append(moved_model.id)
        else:
            moved_instance = target_parent.add(name=part_instance.name, model=moved_model, suppress_kevents=True)
            map_property_instances(part_instance, moved_instance)
            update_part_with_properties(part_instance, moved_instance, name=name)
    else:
        moved_instance = target_parent.add(name=part_instance.name, model=moved_model, suppress_kevents=True)
        map_property_instances(part_instance, moved_instance)
        update_part_with_properties(part_instance, moved_instance, name=name)

    if include_children:
        for sub_instance in part_instance._cached_children:
            move_part_instance(part_instance=sub_instance, target_parent=moved_instance, part_model=sub_instance.model(),
                               name=sub_instance.name, include_children=True)

    return


def update_part_with_properties(part_instance, moved_instance, name=None):
    """

    Parameters
    ----------
    part_instance
    moved_instance

    Returns
    -------

    """
    properties_id_dict = dict()
    properties_name_dict = dict()
    for prop_instance in part_instance.properties:
        if prop_instance._json_data['property_type'] != PropertyType.ATTACHMENT_VALUE:
            moved_prop_instance = __mapping_dictionary[prop_instance.id]
            properties_id_dict[moved_prop_instance.id] = prop_instance.value
            properties_name_dict[moved_prop_instance.name] = prop_instance.value
        else:
            if prop_instance.value:
                attachment_name = prop_instance._json_data['value'].split('/')[-1]
                moved_prop = __mapping_dictionary[prop_instance.id]
                with temp_chdir() as target_dir:
                    full_path = os.path.join(target_dir or os.getcwd(), attachment_name)
                    prop_instance.save_as(filename=full_path)
                    moved_prop.upload(full_path)
    if len(part_instance.properties) > 1:
        moved_instance.update(name=name, update_dict=properties_id_dict, bulk=True, suppress_kevents=True)
    else:
        moved_instance.update(name=name, update_dict=properties_name_dict, bulk=True,
                              suppress_kevents=True)
    return


def map_property_instances(original_part, new_part):
    __mapping_dictionary[original_part.id] = new_part

    # Do the same for each Property of catalog instance, using the 'model' id
    for prop_original in original_part.properties:
        __mapping_dictionary[prop_original.id] = [prop_new for prop_new in new_part.properties if
                                                  __mapping_dictionary[prop_original._json_data['model']].id ==
                                                  prop_new._json_data['model']][0]
