import os
from typing import Optional, Text

from pykechain.enums import PropertyType, Multiplicity
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Part, AnyProperty, Property
from pykechain.utils import temp_chdir

# global variable
__mapping_dictionary = None
__edited_one_many = list()  # type: list
__references = dict()


def get_mapping_dictionary(clean=False) -> dict:
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


def get_edited_one_many(clean=False) -> list:
    """
    Get a temporary helper to help relocating Parts with one to many relationships.

    Only used in the relocation of parts and models.

    :param clean: (optional) boolean flag to reset the list of Parts
    :type clean: bool
    :return: singleton list (persistent in the script) for tracking purposes
    """
    global __edited_one_many
    if not __edited_one_many or clean:
        __edited_one_many = list()
    return __edited_one_many


def get_references(clean=False) -> dict:
    """
    Get a temporary helper dictionary to store references (values) per property (keys).

    :param clean: (optional) boolean flag to reset the list of references
    :type clean: bool
    :return: singleton dictionary (persistent in the script) for tracking purposes
    """
    global __references
    if not __references or clean:
        __references = dict()
    return __references


def get_illegal_targets(part: Part, include: set):
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
    list_of_illegal_targets.update({c.id for c in part.all_children()})
    return list_of_illegal_targets


def relocate_model(
        part: Part,
        target_parent: Part,
        name: Optional[Text] = None,
        include_children: Optional[bool] = True
) -> Part:
    """
    Move the `Part` model under a target parent `Part` model.

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
        raise IllegalArgumentError("Cannot relocate part `{}` under target parent `{}`, because the target is part of "
                                   "its descendants".format(part.name, target_parent.name))

    if include_children:
        part.populate_descendants()
        
    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = "CLONE - {}".format(part.name)

    # Recursively create the part model copy
    moved_part_model = move_part_model(
        part=part,
        target_parent=target_parent,
        name=name,
        include_children=include_children,
    )

    # Try to update references to parts by updating the UUID via the mapping dictionary
    Property.set_bulk_update(True)
    mapping = get_mapping_dictionary()
    for prop_old, references_old in get_references().items():  # type: (AnyProperty, list)
        # try to map to a new ID, default to the existing reference ID
        references_new = [mapping.get(r, r) for r in references_old]
        prop_new = mapping.get(prop_old.id)
        prop_new.value = references_new
    Property.update_values(client=part._client)

    return moved_part_model


def move_part_model(
        part: Part,
        target_parent: Part,
        name: Text,
        include_children: bool,
) -> Part:
    """
    Copy the `Part` model under a target parent `Part` model, recursively.

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
    
    # The description cannot be added when creating a model, so edit the model after creation.
    part_desc = part.description
    moved_part_model = target_parent.add_model(name=name, multiplicity=part.multiplicity)
    if part_desc:
        moved_part_model.edit(description=str(part_desc))

    # Map the current part model id with newly created part model Object
    get_mapping_dictionary().update({part.id: moved_part_model})

    # Loop through properties and retrieve their type, description and unit
    list_of_properties_sorted_by_order = part.properties
    list_of_properties_sorted_by_order.sort(key=lambda x: x._json_data['order'])
    for prop in list_of_properties_sorted_by_order:  # type: AnyProperty

        # For KE-chain 3 (PIM2) we have value_options instead of options.
        if prop._client.match_app_version(label='pim', version='>=3.0.0'):
            options = prop._json_data.get('value_options')
        else:
            options = prop._json_data.get('options')

        if prop.type == PropertyType.REFERENCES_VALUE:
            get_references()[prop] = prop.value_ids()
            prop_value = None
        else:
            prop_value = prop._value

        moved_prop = moved_part_model.add_property(
            name=prop.name,
            description=prop.description,
            property_type=prop.type,
            default_value=prop_value,
            unit=prop.unit,
            options=options,
        )

        # For attachment properties, the value is a file that must be transferred manually
        if prop.type == PropertyType.ATTACHMENT_VALUE and prop.has_value():
            with temp_chdir() as target_dir:
                full_path = os.path.join(target_dir or os.getcwd(), prop.filename)
                prop.save_as(filename=full_path)
                moved_prop.upload(full_path)

        # Map the current property model id with newly created property model Object
        get_mapping_dictionary()[prop.id] = moved_prop

    # Now copy the sub-tree of the part
    if include_children:
        # For each part, recursively run this function
        for sub_part in part.children():
            move_part_model(
                part=sub_part,
                target_parent=moved_part_model,
                name=sub_part.name,
                include_children=include_children,
            )
            
    return moved_part_model


def relocate_instance(
        part: Part,
        target_parent: Part,
        name: Optional[Text] = None,
        include_children: Optional[bool] = True,
) -> Part:
    """
    Move the `Part` instance under a target parent `Part` instance.

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

    if include_children:
        part_model.populate_descendants()

    # To relocate an instance, its model has to go first
    relocate_model(
        part=part_model,
        target_parent=target_parent_model,
        name=part_model.name,
        include_children=include_children,
    )
    get_references(clean=True)

    # This function will move the part instance under the target_parent instance, and its children if required.
    moved_instance = move_part_instance(
        part_instance=part,
        target_parent=target_parent,
        part_model=part_model,
        name=name,
        include_children=include_children,
    )

    # Try to update references to parts by updating the UUID via the mapping dictionary
    Property.set_bulk_update(True)
    mapping = get_mapping_dictionary()
    for prop_old, references_old in get_references().items():  # type: (AnyProperty, list)
        # try to map to a new ID, default to the existing reference ID
        references_new = [mapping.get(r, r) for r in references_old]
        prop_new = mapping.get(prop_old.id)
        prop_new.value = references_new
    Property.update_values(client=part._client)

    return moved_instance


def move_part_instance(
        part_instance: Part,
        target_parent: Part,
        part_model: Part,
        name: Optional[Text] = None,
        include_children: Optional[bool] = True
) -> Part:
    """
    Copy the `Part` instance to target parent and updates the properties based on the original part instance.

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
    if not name:
        name = part_instance.name

    # Retrieve the model of the future part to be created
    moved_model = get_mapping_dictionary()[part_model.id]

    # Now act based on multiplicity
    if moved_model.multiplicity == Multiplicity.ONE:
        # If multiplicity is 'Exactly 1', that means the instance was automatically created with the model.
        moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
    elif moved_model.multiplicity == Multiplicity.ONE_MANY:
        # If multiplicity is '1 or more', that means one instance has automatically been created with the model.
        # Store the model in a list, in case there are multiple instance that need to be recreated.
        if moved_model.id not in get_edited_one_many():
            moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
            get_edited_one_many().append(moved_model.id)
        else:
            moved_instance = target_parent.add(name=name, model=moved_model, suppress_kevents=True)
    else:
        # If multiplicity is '0 or more' or '0 or 1', it means no instance has been created automatically with the
        # model, so then everything must be created and then updated.
        moved_instance = target_parent.add(name=name, model=moved_model, suppress_kevents=True)

    # Update properties of the instance
    map_property_instances(part_instance, moved_instance)
    moved_instance = update_part_with_properties(part_instance, moved_instance, name=str(name))

    if include_children:
        sub_models = {child.id: child for child in part_model.children()}
        # Recursively call this function for every descendant. Keep the name of the original sub-instance.
        for sub_instance in part_instance.children():
            move_part_instance(
                part_instance=sub_instance,
                target_parent=moved_instance,
                part_model=sub_models.get(sub_instance.model_id, sub_instance.model()),
                name=sub_instance.name,
                include_children=True,
            )

    return moved_instance


def update_part_with_properties(
        part_instance: Part,
        moved_instance: Part,
        name: Optional[Text] = None,
) -> Part:
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
    # Instantiate an empty dictionary later used to map {property.id: property.value} in order to update the part
    # in one go
    properties_id_dict = dict()
    for prop_instance in part_instance.properties:  # type: AnyProperty
        moved_prop_instance = get_mapping_dictionary()[prop_instance.id]

        # Do different magic if there is an attachment property and it has a value
        if prop_instance.type == PropertyType.ATTACHMENT_VALUE:
            if prop_instance.has_value():
                with temp_chdir() as target_dir:
                    full_path = os.path.join(target_dir or os.getcwd(), prop_instance.filename)
                    prop_instance.save_as(filename=full_path)
                    moved_prop_instance.upload(full_path)
            else:
                moved_prop_instance.clear()

        # For a reference value property, add the id's of the part referenced {property.id: [part1.id, part2.id, ...]},
        # if there is part referenced at all.
        elif prop_instance.type == PropertyType.REFERENCES_VALUE:
            if prop_instance.has_value():
                properties_id_dict[moved_prop_instance.id] = [ref_part.id for ref_part in prop_instance.value]
        elif prop_instance.type == PropertyType.SINGLE_SELECT_VALUE:
            if prop_instance.model().options:
                if prop_instance.value in prop_instance.model().options:
                    properties_id_dict[moved_prop_instance.id] = prop_instance.value
        elif prop_instance.type == PropertyType.MULTI_SELECT_VALUE:
            if prop_instance.value:
                if all(value in prop_instance.model().options for value in prop_instance.value):
                    properties_id_dict[moved_prop_instance.id] = prop_instance.value
        else:
            properties_id_dict[moved_prop_instance.id] = prop_instance.value

    # Update the name and property values in one go.
    moved_instance.update(name=str(name), update_dict=properties_id_dict, bulk=True, suppress_kevents=True)

    return moved_instance


def map_property_instances(original_part: Part, new_part: Part) -> None:
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
        get_mapping_dictionary()[prop_original.id] = [
            prop_new for prop_new in new_part.properties if
            get_mapping_dictionary()[prop_original.model_id].id == prop_new.model_id][0]
