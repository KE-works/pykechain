import os

from pykechain.enums import PropertyType, Multiplicity
from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import temp_chdir

# global variable
__mapping_dictionary = None
__edited_one_many = list()  # type: list


def get_mapping_dictionary(clean=False):
    """
    Get a temporary helper to map some keys to some values. Mainly used in the relocation of parts and models.

    :param clean: (optional) boolean flag to reset the mapping dictionary
    :type clean: bool
    :return: singleton dictionary (persistent in the script) for mapping use.
    """
    global __mapping_dictionary
    if not __mapping_dictionary or clean:
        __mapping_dictionary = dict()
    return __mapping_dictionary


def get_edited_one_many(clean=False):
    """
    Get a temporary helper to help relocating Parts with one to many relationships.

    Only used in the relocation of parts and models.

    :param clean: (optional) boolean flag to reset the mapping dictionary
    :type clean: bool
    :return: singleton dictionary (persistent in the script) for mapping use.
    """
    global __edited_one_many
    if not __edited_one_many or clean:
        __edited_one_many = list()
    return __edited_one_many


def relocate_model(part, target_parent, name=None, include_children=True):
    """
    Move the `Part` model to target parent.

    .. versionadded:: 2.3

    :param part: `Part` object to be moved
    :type part: :class:`Part`
    :param target_parent: `Part` object under which the desired `Part` is moved
    :type target_parent: :class:`Part`
    :param name: how the moved top-level `Part` should be called
    :type name: basestring
    :param include_children: True to move also the descendants of `Part`. If False, the children will be lost.
    :type include_children: bool
    :return: moved :class: Part model.
    :raises IllegalArgumentError: if target_parent is descendant of part
    """
    if target_parent.id in get_illegal_targets(part, include={part.id}):
        raise IllegalArgumentError('cannot relocate part "{}" under target parent "{}", because the target is part of '
                                   'its descendants'.format(part.name, target_parent.name))

    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = "CLONE - {}".format(part.name)

    # The description cannot be added when creating a model, so edit the model after creation.
    part_desc = part._json_data['description']
    moved_part_model = target_parent.add_model(name=name, multiplicity=part.multiplicity)
    if part_desc:
        moved_part_model.edit(description=str(part_desc))

    # Map the current part model id with newly created part model Object
    get_mapping_dictionary().update({part.id: moved_part_model})

    # Loop through properties and retrieve their type, description and unit
    list_of_properties_sorted_by_order = part.properties
    list_of_properties_sorted_by_order.sort(key=lambda x: x._json_data['order'])
    for prop in list_of_properties_sorted_by_order:
        prop_type = prop._json_data.get('property_type')
        desc = prop._json_data.get('description')
        unit = prop._json_data.get('unit')
        options = prop._json_data.get('options')

        # On "Part references" properties, the models referenced also need to be added
        if prop_type == PropertyType.REFERENCES_VALUE:
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
                                                       default_value=prop.value, unit=unit, options=options)

        # Map the current property model id with newly created property model Object
        get_mapping_dictionary()[prop.id] = moved_prop

    # Now copy the sub-tree of the part
    if include_children:
        # Populate the part so multiple children retrieval is not needed
        part.populate_descendants()
        # For each part, recursively run this function
        for sub_part in part._cached_children:
            relocate_model(part=sub_part, target_parent=moved_part_model, name=sub_part.name,
                           include_children=include_children)
    return moved_part_model


def get_illegal_targets(part, include):
    """
    Retrieve the illegal parent parts where `Part` can be moved/copied.

    :param part: `Part` to be moved/copied.
    :type part: :class:`Part`
    :param include: `Set` object with id's to be avoided as target parent `Part`
    :type include: set
    :return: `List` object of illegal id's
    :rtype: list
    """
    list_of_illegal_targets = include or set()
    for descendant in part.children(descendants='children'):
        list_of_illegal_targets.add(descendant.id)
    return list_of_illegal_targets


def relocate_instance(part, target_parent, name=None, include_children=True):
    """
    Move the `Part` instance to target parent.

    .. versionadded:: 2.3

    :param part: `Part` object to be moved
    :type part: :class:`Part`
    :param target_parent: `Part` object under which the desired `Part` is moved
    :type target_parent: :class:`Part`
    :param name: how the moved top-level `Part` should be called
    :type name: basestring
    :param include_children: True to move also the descendants of `Part`. If False, the children will be lost.
    :type include_children: bool
    :return: moved :class: `Part` instance
    """
    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = "CLONE - {}".format(part.name)
    # Initially the model of the part needs to be recreated under the model of the target_parent. Retrieve them.
    part_model = part.model()
    target_parent_model = target_parent.model()

    # Call the move_part() function for those models.
    relocate_model(part=part_model, target_parent=target_parent_model, name=part_model.name,
                   include_children=include_children)

    # Populate the descendants of the Part (category=Instance), in order to avoid to retrieve children for every
    # level and save time. Only need it the children should be included.
    if include_children:
        part.populate_descendants()

    # This function will move the part instance under the target_parent instance, and its children if required.
    moved_instance = move_part_instance(part_instance=part, target_parent=target_parent, part_model=part_model,
                                        name=name, include_children=include_children)
    return moved_instance


def move_part_instance(part_instance, target_parent, part_model, name=None, include_children=True):
    """
    Move the `Part` instance to target parent and updates the properties based on the original part instance.

    .. versionadded:: 2.3

    :param part_instance: `Part` object to be moved
    :type part_instance: :class:`Part`
    :param part_model: `Part` object representing the model of part_instance
    :type part_model: :class: `Part`
    :param target_parent: `Part` object under which the desired `Part` is moved
    :type target_parent: :class:`Part`
    :param name: how the moved top-level `Part` should be called
    :type name: basestring
    :param include_children: True to move also the descendants of `Part`. If False, the children will be lost.
    :type include_children: bool
    :return: moved :class: `Part` instance
    """
    # If no specific name has been required, then call in as Clone of the part_instance.
    if not name:
        name = part_instance.name

    # Retrieve the model of the future part to be created
    moved_model = get_mapping_dictionary()[part_model.id]

    # Now act based on multiplicity
    if moved_model.multiplicity == Multiplicity.ONE:
        # If multiplicity is 'Exactly 1', that means the instance was automatically created with the model, so just
        # retrieve it, map the original instance with the moved one and update the name and property values.
        moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
        map_property_instances(part_instance, moved_instance)
        moved_instance = update_part_with_properties(part_instance, moved_instance, name=str(name))
    elif moved_model.multiplicity == Multiplicity.ONE_MANY:
        # If multiplicity is '1 or more', that means one instance has automatically been created with the model, so
        # retrieve it, map the original instance with the moved one and update the name and property values. Store
        # the model in a list, in case there are multiple instance those need to be recreated.
        if target_parent.id not in get_edited_one_many():
            moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
            map_property_instances(part_instance, moved_instance)
            moved_instance = update_part_with_properties(part_instance, moved_instance, name=str(name))
            get_edited_one_many().append(target_parent.id)
        else:
            moved_instance = target_parent.add(name=part_instance.name, model=moved_model, suppress_kevents=True)
            map_property_instances(part_instance, moved_instance)
            moved_instance = update_part_with_properties(part_instance, moved_instance, name=str(name))
    else:
        # If multiplicity is '0 or more' or '0 or 1', it means no instance has been created automatically with the
        # model, so then everything must be created and then updated.
        moved_instance = target_parent.add(name=name, model=moved_model, suppress_kevents=True)
        map_property_instances(part_instance, moved_instance)
        moved_instance = update_part_with_properties(part_instance, moved_instance, name=str(name))

    # If include_children is True, then recursively call this function for every descendant. Keep the name of the
    # original sub-instance.
    if include_children:
        for sub_instance in part_instance._cached_children:
            move_part_instance(part_instance=sub_instance, target_parent=moved_instance,
                               part_model=sub_instance.model(),
                               name=sub_instance.name, include_children=True)

    return moved_instance


def update_part_with_properties(part_instance, moved_instance, name=None):
    """
    Update the newly created part and its properties based on the original one.

    :param part_instance: `Part` object to be copied
    :type part_instance: :class:`Part`
    :param moved_instance: `Part` object copied
    :type moved_instance: :class:`Part`
    :param name: Name of the updated part
    :type name: basestring
    :return: moved :class: `Part` instance
    """
    # Instantiate and empty dictionary later used to map {property.id: property.value} in order to update the part
    # in one go
    properties_id_dict = dict()
    for prop_instance in part_instance.properties:
        # Do different magic if there is an attachment property and it has a value
        if prop_instance._json_data['property_type'] == PropertyType.ATTACHMENT_VALUE:
            moved_prop = get_mapping_dictionary()[prop_instance.id]
            if prop_instance.value:
                attachment_name = prop_instance._json_data['value'].split('/')[-1]
                with temp_chdir() as target_dir:
                    full_path = os.path.join(target_dir or os.getcwd(), attachment_name)
                    prop_instance.save_as(filename=full_path)
                    moved_prop.upload(full_path)
            else:
                moved_prop.clear()
        # For a reference value property, add the id's of the part referenced {property.id: [part1.id, part2.id, ...]},
        # if there is part referenced at all.
        elif prop_instance._json_data['property_type'] == PropertyType.REFERENCES_VALUE:
            if prop_instance.value:
                moved_prop_instance = get_mapping_dictionary()[prop_instance.id]
                properties_id_dict[moved_prop_instance.id] = [ref_part.id for ref_part in prop_instance.value]
        else:
            moved_prop_instance = get_mapping_dictionary()[prop_instance.id]
            properties_id_dict[moved_prop_instance.id] = prop_instance.value
    # Update the name and property values in one go.
    moved_instance.update(name=str(name), update_dict=properties_id_dict, bulk=True, suppress_kevents=True)
    return moved_instance


def map_property_instances(original_part, new_part):
    """
    Map the id of the original part with the `Part` object of the newly created one.

    Updated the singleton `mapping dictionary` with the new mapping table values.

    :param original_part: `Part` object to be copied/moved
    :type original_part: :class:`Part`
    :param new_part: `Part` object copied/moved
    :type new_part: :class:`Part`
    :return: None
    """
    # Map the original part with the new one
    get_mapping_dictionary()[original_part.id] = new_part

    # Do the same for each Property of original part instance, using the 'model' id and the get_mapping_dictionary
    for prop_original in original_part.properties:
        get_mapping_dictionary()[prop_original.id] = [prop_new for prop_new in new_part.properties if
                                                      get_mapping_dictionary()[prop_original._json_data['model']].id ==
                                                      prop_new._json_data['model']][0]
