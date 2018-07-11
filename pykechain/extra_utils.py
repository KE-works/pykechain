import os

from pykechain.enums import Category, PropertyType, Multiplicity
from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import temp_chdir

# global variable
__mapping_dictionary = None
__edited_one_many = list()


def get_mapping_dictionary(clean=False):
    """
    Get a temprorary helper to map some keys to some values. Mainly used in the relocation of parts and models.
    
    :param clean: (optional) boolean flag to reset the mapping dictionary  
    :return: singleton dictionary (persistent in the script) for mapping use.
    """
    global __mapping_dictionary
    if not __mapping_dictionary or clean:
        __mapping_dictionary = dict()
    return __mapping_dictionary

def get_edited_one_many(clean=False):
    """
    Get a temprorary helper to help relocating Parts with one to many relationships. 
    Only used in the relocation of parts and models.
    
    :param clean: (optional) boolean flag to reset the mapping dictionary  
    :return: singleton dictionary (persistent in the script) for mapping use.
    """
    global __edited_one_many
    if not __edited_one_many or clean:
        __edited_one_many = dict()
    return __edited_one_many



def relocate_model(part, target_parent, name=None, include_children=True):
    """

    :param part:
    :param target_parent:
    :param name:
    :param include_children:
    :return:
    """
    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = "CLONE - {}".format(part.name)
    # First case: Add a model to another model
    if part.category != Category.MODEL and target_parent.category != Category.MODEL:
        # Cannot add a model under an instance or vice versa
        raise IllegalArgumentError('part and target_parent must be both MODELS')

    # The description cannot be added when creating a model, so edit the model after creation.
    part_desc = part._json_data['description']
    moved_part_model = target_parent.add_model(name=name, multiplicity=part.multiplicity)
    if part_desc:
        moved_part_model.edit(description=part_desc)

    # Map the current part model id with newly created part model Object
    get_mapping_dictionary().update({part.id: moved_part_model})

    # TODO () Include the validators
    # Loop through properties and retrieve their type, description and unit
    for prop in part.properties:
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
    l = include or list()
    l.append([c.id for c in part.children()])
    return l


def relocate_instance(part, target_parent, name=None, include_children=True):
    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if target_parent.id in get_illegal_targets(part, include=[target_parent.id, part.id]):
        raise IllegalArgumentError()

    if not name:
        name = "CLONE - {}".format(part.name)

    if part.category == Category.INSTANCE and target_parent.category == Category.INSTANCE:
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
    else:
        # Cannot add a model under an instance or vice versa
        raise IllegalArgumentError('part and target_parent must be both MODELS')


def move_part_instance(part_instance, target_parent, part_model, name=None, include_children=True):
    """

    :param part_instance:
    :param target_parent:
    :param part_model:
    :param name:
    :param include_children:
    :return:
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
        update_part_with_properties(part_instance, moved_instance, name=name)
    elif moved_model.multiplicity == Multiplicity.ONE_MANY:
        # If multiplicity is '1 or more', that means one instance has automatically been created with the model, so
        # retrieve it, map the original instance with the moved one and update the name and property values. Store
        # the model in a list, in case there are multiple instance those need to be recreated.
        if target_parent.id not in get_edited_one_many():
            moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
            map_property_instances(part_instance, moved_instance)
            update_part_with_properties(part_instance, moved_instance, name=name)
            get_edited_one_many().append(target_parent.id)
        else:
            moved_instance = target_parent.add(name=part_instance.name, model=moved_model, suppress_kevents=True)
            map_property_instances(part_instance, moved_instance)
            update_part_with_properties(part_instance, moved_instance, name=name)
    else:
        # If multiplicity is '0 or more' or '0 or 1', it means no instance has been created automatically with the
        # model, so then everything must be created and then updated.
        moved_instance = target_parent.add(name=part_instance.name, model=moved_model, suppress_kevents=True)
        map_property_instances(part_instance, moved_instance)
        update_part_with_properties(part_instance, moved_instance, name=name)

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

    :param part_instance:
    :param moved_instance:
    :param name:
    :return:
    """
    # Instantiate and empty dictionary later used to map {property.id: property.value} in order to update the part
    # in one go
    properties_id_dict = dict()
    for prop_instance in part_instance.properties:
        # Do different magic if there is an attachment property and it has a value
        if prop_instance._json_data['property_type'] == PropertyType.ATTACHMENT_VALUE:
            if prop_instance.value:
                attachment_name = prop_instance._json_data['value'].split('/')[-1]
                moved_prop = get_mapping_dictionary()[prop_instance.id]
                with temp_chdir() as target_dir:
                    full_path = os.path.join(target_dir or os.getcwd(), attachment_name)
                    prop_instance.save_as(filename=full_path)
                    moved_prop.upload(full_path)
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
    moved_instance.update(name=name, update_dict=properties_id_dict, bulk=True, suppress_kevents=True)
    return


def map_property_instances(original_part, new_part):
    """

    :param original_part:
    :param new_part:
    :return:
    """
    # Map the original part with the new one
    get_mapping_dictionary()[original_part.id] = new_part

    # Do the same for each Property of original part instance, using the 'model' id and the get_mapping_dictionary
    for prop_original in original_part.properties:
        get_mapping_dictionary()[prop_original.id] = [prop_new for prop_new in new_part.properties if
                                                  get_mapping_dictionary()[prop_original._json_data['model']].id ==
                                                  prop_new._json_data['model']][0]
