import os
import tempfile
import warnings
from collections import namedtuple
from typing import Optional, List, Any

from pykechain import Client
from pykechain.enums import PropertyType, Multiplicity, Category
from pykechain.exceptions import IllegalArgumentError, NotFoundError, MultipleFoundError
from pykechain.models import Part, AnyProperty, Property, PropertyValueFilter
from pykechain.utils import temp_chdir

# global variable
__mapping_dictionary = None
__edited_one_many: list = list()
__references = dict()
__attachments = list()

_InstanceCopy = namedtuple(
    "InstanceCopyAttributes",
    field_names=[
        "instance_original",
        "model_original",
        "target_parent_instance",
        "name",
    ],
)


# TODO Deprecate original utility functions in July 2021


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


def get_attachments(clean=False) -> list:
    """
    Get a temporary helper list to store attachment properties.

    :param clean: (optional) boolean flag to reset the list
    :type clean: bool
    :return: singleton list (persistent in the script) for tracking purposes
    """
    global __attachments
    if not __attachments or clean:
        __attachments = list()
    return __attachments


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
    mapping = get_mapping_dictionary()
    mapping[original_part.id] = new_part

    # Do the same for each Property of original part instance, using the 'model' id and the get_mapping_dictionary
    for prop_original in original_part.properties:
        mapping[prop_original.id] = [
            prop_new
            for prop_new in new_part.properties
            if mapping[prop_original.model_id].id == prop_new.model_id
        ][0]


def relocate_model(
    part: Part,
    target_parent: Part,
    name: Optional[str] = None,
    include_children: Optional[bool] = True,
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
    warnings.warn(
        "`relocate_model` is no longer in use and will be deprecated in July 2021.",
        PendingDeprecationWarning,
    )

    if target_parent.id in get_illegal_targets(part, include={part.id}):
        raise IllegalArgumentError(
            "Cannot relocate part `{}` under target parent `{}`, because the target is part of "
            "its descendants".format(part.name, target_parent.name)
        )

    if include_children:
        part.populate_descendants()

    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = f"CLONE - {part.name}"

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
    for (
        prop_old,
        references_old,
    ) in get_references().items():  # type: (AnyProperty, list)
        prop_new = mapping.get(prop_old.id)

        # try to map to a new ID, default to the existing reference ID
        references_new = [mapping.get(r, r) for r in references_old]
        prop_new.value = references_new
    Property.update_values(client=part._client)

    return moved_part_model


def move_part_model(
    part: Part,
    target_parent: Part,
    name: str,
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
    """
    warnings.warn(
        "`move_part_model` is no longer in use and will be deprecated in July 2021.",
        PendingDeprecationWarning,
    )
    return _copy_part_model(
        part=part,
        target_parent=target_parent,
        name=name,
        include_children=include_children,
    )


def _copy_part_model(
    part: Part,
    target_parent: Part,
    name: str,
    include_children: bool,
) -> Part:
    """
    Copy the `Part` model under a target parent `Part` model, including its descendants recursively.

    .. versionadded:: 2.3

    :param part: `Part` object to be copied
    :type part: :class:`Part`
    :param target_parent: `Part` object under which the desired `Part` is copied
    :type target_parent: :class:`Part`
    :param name: how the copied top-level `Part` should be called
    :type name: basestring
    :param include_children: True to also copy the descendants of `Part`. If False, the children will be lost.
    :type include_children: bool
    :return: moved :class: Part model.
    """
    property_fvalues = list()
    for prop in part.properties:  # type: AnyProperty
        property_values = dict(
            name=prop.name,
            description=prop.description,
            property_type=prop.type,
            value=_get_property_value(prop),
            unit=prop.unit,
            value_options=prop._options,
        )
        property_values = {k: v for k, v in property_values.items() if v is not None}
        property_fvalues.append(property_values)

    # Create the model and its properties in a single request
    moved_part_model = part._client.create_model_with_properties(
        name=name,
        parent=target_parent,
        multiplicity=part.multiplicity,
        properties_fvalues=property_fvalues,
    )

    # Map the current IDs with newly created objects
    get_mapping_dictionary().update({part.id: moved_part_model})
    for prop, moved_prop in zip(part.properties, moved_part_model.properties):
        get_mapping_dictionary()[prop.id] = moved_prop

    # The description cannot be added when creating a model, so edit the model after creation.
    if part.description:
        moved_part_model.edit(description=str(part.description))

    # Recursively, copy the sub-tree of the model
    if include_children:
        for sub_part in part.children():
            _copy_part_model(
                part=sub_part,
                target_parent=moved_part_model,
                name=sub_part.name,
                include_children=include_children,
            )

    return moved_part_model


def relocate_instance(
    part: Part,
    target_parent: Part,
    name: Optional[str] = None,
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
    warnings.warn(
        "`relocate_instance` is no longer in use and will be deprecated in July 2021.",
        PendingDeprecationWarning,
    )

    # First, if the user doesn't provide the name, then just use the default "Clone - ..." name
    if not name:
        name = f"CLONE - {part.name}"

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
    for (
        prop_old,
        references_old,
    ) in get_references().items():  # type: (AnyProperty, list)
        prop_new = mapping.get(prop_old.id)

        # try to map to a new ID, default to the existing reference ID
        references_new = [mapping.get(r, r) for r in references_old]
        prop_new.value = references_new
    Property.update_values(client=part._client)

    return moved_instance


def move_part_instance(
    part_instance: Part,
    target_parent: Part,
    part_model: Part,
    name: Optional[str] = None,
    include_children: Optional[bool] = True,
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
    warnings.warn(
        "`move_part_instance` is no longer in use and will be deprecated in July 2021.",
        PendingDeprecationWarning,
    )

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
        # This first instance has to be used, but only once. Therefore, store the model in a global list after doing so.
        if moved_model.id not in get_edited_one_many():
            moved_instance = moved_model.instances(parent_id=target_parent.id)[0]
            get_edited_one_many().append(moved_model.id)
        else:
            moved_instance = target_parent.add(
                name=name, model=moved_model, suppress_kevents=True
            )
    else:
        # If multiplicity is '0 or more' or '0 or 1', it means no instance has been created automatically with the
        # model, so then everything must be created and then updated.
        moved_instance = target_parent.add(
            name=name, model=moved_model, suppress_kevents=True
        )

    # Update properties of the instance
    map_property_instances(original_part=part_instance, new_part=moved_instance)
    update_part_with_properties(part_instance, moved_instance, name=str(name))

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
    name: Optional[str] = None,
) -> Part:
    """
    Update the properties of the `moved_instance` based on the original `part_instance`.

    :param part_instance: `Part` object to be copied
    :type part_instance: :class:`Part`
    :param moved_instance: `Part` object copied
    :type moved_instance: :class:`Part`
    :param name: Name of the updated part
    :type name: basestring
    :return: moved :class: `Part` instance
    """
    warnings.warn(
        "`update_part_with_properties` is no longer in use and will be deprecated in July 2021.",
        PendingDeprecationWarning,
    )

    # Instantiate an empty dictionary used to collect all property values in order to update the part in one go.
    properties_id_dict = dict()
    for prop_instance in part_instance.properties:  # type: AnyProperty
        moved_prop_instance = get_mapping_dictionary()[prop_instance.id]

        # Do different magic if there is an attachment property and it has a value
        if prop_instance.type == PropertyType.ATTACHMENT_VALUE:
            if prop_instance.has_value():
                with temp_chdir() as target_dir:
                    full_path = os.path.join(
                        target_dir or os.getcwd(), prop_instance.filename
                    )
                    prop_instance.save_as(filename=full_path)
                    moved_prop_instance.upload(full_path)
            else:
                moved_prop_instance.clear()

        # For a reference value property, add the id's of the part referenced {property.id: [part1.id, part2.id, ...]},
        # if there is part referenced at all.
        elif prop_instance.type == PropertyType.REFERENCES_VALUE:
            if prop_instance.has_value():
                get_references()[prop_instance] = prop_instance.value_ids()

        elif prop_instance.type == PropertyType.SINGLE_SELECT_VALUE:
            if prop_instance.model().options:
                if prop_instance.value in prop_instance.model().options:
                    properties_id_dict[moved_prop_instance.id] = prop_instance.value

        elif prop_instance.type == PropertyType.MULTI_SELECT_VALUE:
            if prop_instance.has_value():
                if all(
                    value in prop_instance.model().options
                    for value in prop_instance.value
                ):
                    properties_id_dict[moved_prop_instance.id] = prop_instance.value

        else:
            properties_id_dict[moved_prop_instance.id] = prop_instance.value

    # Update the name and property values in one go.
    moved_instance.update(
        name=str(name), update_dict=properties_id_dict, bulk=True, suppress_kevents=True
    )

    return moved_instance


def _copy_part(
    part: Part,
    target_parent: Part,
    name: Optional[str] = None,
    include_children: Optional[bool] = True,
    include_instances: Optional[bool] = True,
) -> Part:
    """
    Copy `part` below `target_parent`, optionally including all child Parts.

    Distinguish between `part` of different category:
    Part MODELS simply need a copy of themselves, and optionally copies of their instances.
    Part INSTANCES first need to have a copy of their part MODEL prior to a copy of themselves.

    :param part: Part to copy
    :param target_parent: Part to copy below
    :param name: (O) new name of the `part` copy
    :param include_children: (O) include the descendants of `part`, defaults to True
    :param include_instances: (O) In case of `part` being of category MODEL, include the instance Parts of that model.
        WARNING: By default, every instance is created per instance of the `target_parent`.
    :return: copy of `part`
    :rtype Part
    """
    get_mapping_dictionary(clean=True)
    get_edited_one_many(clean=True)
    get_references(clean=True)
    get_attachments(clean=True)

    if part.category == Category.INSTANCE:
        model = part.model()
        target_parent_model = target_parent.model()
        name_model = model.name

        instances = [
            _InstanceCopy(
                instance_original=part,
                target_parent_instance=target_parent,
                model_original=model,
                name=part.name if name is None else name,
            )
        ]

    else:  # part.category == Category.MODEL

        model = part
        target_parent_model = target_parent
        name_model = part.name if name is None else name

        if include_instances:
            try:
                target_parent_instance = target_parent_model.instance()
            except NotFoundError:
                raise IllegalArgumentError(
                    "Cannot copy part model `{}` including instances, since the target_parent"
                    " model `{}` has no instance to act as parent for the instances.".format(
                        model, target_parent_model
                    )
                )
            except MultipleFoundError:
                raise IllegalArgumentError(
                    "Cannot copy part model `{}` including instances, since the target_parent"
                    " model `{}` has multiple instances, making the parent for the instances"
                    " ambiguous.".format(model, target_parent_model)
                )

            instances = [
                _InstanceCopy(
                    instance_original=instance,
                    target_parent_instance=target_parent_instance,
                    model_original=model,
                    name=instance.name,
                )
                for instance in model.instances()
            ]
        else:
            instances = []

    # Verify if the target_parent is not below the part
    model.populate_descendants()
    if target_parent_model.id in get_illegal_targets(model, include={model.id}):
        raise IllegalArgumentError(
            "Cannot relocate part `{}` under target parent `{}`, because the target is part of "
            "its descendants".format(model.name, target_parent.name)
        )

    copied_model = _copy_part_model(
        part=model,
        target_parent=target_parent_model,
        name=name_model,
        include_children=include_children,
    )

    Property.set_bulk_update(True)
    _update_references()
    Property.update_values(client=copied_model._client, use_bulk_update=True)

    copied_instances = _copy_instances_recursive(
        client=copied_model._client,
        instances=instances,
        include_children=include_children,
    )

    mapping = get_mapping_dictionary()
    attachment_properties = get_attachments()
    for prop_original in attachment_properties:
        prop_new = mapping[prop_original.id]
        if prop_original.has_value():
            with tempfile.TemporaryDirectory() as target_dir:
                full_path = os.path.join(target_dir, prop_original.filename)
                prop_original.save_as(filename=full_path)
                prop_new.upload(full_path)

    _update_references()
    Property.update_values(client=copied_model._client)

    return copied_model if part.category == Category.MODEL else copied_instances[0]


def _copy_instances_recursive(
    client: Client,
    instances: List[_InstanceCopy],
    include_children: bool,
) -> List[Part]:
    """
    Create new Part instances in bulk, recursively.

    Reference and Attachment properties have to be updated outside this function.

    :param client: Client object
    :param instances: list of _Instance instances.
    :param include_children: whether to create instance parts
    :return: list of new Part instances
    :rtype list
    """
    if not instances:
        return []

    mapping = get_mapping_dictionary()
    create_request = []  # request for the bulk create
    created_instances_indices = []  # indices in a list
    original_instances = []  # part instances that require a copy
    new_instances = []  # all new Part objects

    for index, i in enumerate(instances):
        model_new = get_mapping_dictionary()[i.model_original.id]
        existing_instance = None

        if model_new.multiplicity == Multiplicity.ONE:
            # If multiplicity is 'Exactly 1', that means the instance was automatically created with the model.
            existing_instance = model_new.instances(
                parent_id=i.target_parent_instance.id
            )[0]

        elif model_new.multiplicity == Multiplicity.ONE_MANY:
            # If multiplicity is '1 or more', that means one instance has automatically been created with the model.
            # This first instance has to be used, but only once. Therefore, store the model in a global list after
            # doing so.
            if model_new.id not in get_edited_one_many():
                existing_instance = model_new.instances(
                    parent_id=i.target_parent_instance.id
                )[0]
                get_edited_one_many().append(model_new.id)
        else:
            # If multiplicity is '0 or more' or '0 or 1', no instance has been created automatically with the model.
            pass

        if existing_instance:
            new_instances.append(existing_instance)
            map_property_instances(
                original_part=i.instance_original, new_part=existing_instance
            )

            if i.name != existing_instance.name:
                existing_instance.edit(name=i.name)

            # part already exists, but properties need to be updated
            for prop_original in i.instance_original.properties:
                prop = mapping.get(prop_original.id)
                prop.value = _get_property_value(prop_original)
        else:
            new_instances.append(None)
            created_instances_indices.append(index)
            original_instances.append(i)

            properties = []
            for prop in i.instance_original.properties:  # type: AnyProperty
                prop_value = _get_property_value(prop)
                if prop_value is not None:
                    properties.append(
                        dict(
                            name=prop.name,
                            value=prop_value,
                            model_id=mapping[prop.model_id].id,
                        )
                    )

            create_request.append(
                dict(
                    name=i.name,
                    parent_id=i.target_parent_instance.id,
                    model_id=model_new.id,
                    properties=properties,
                )
            )

    if create_request:
        created_instances = client._create_parts_bulk(
            parts=create_request,
            asynchronous=False,
            retrieve_instances=True,
        )
        for index, new_instance, i in zip(
            created_instances_indices, created_instances, original_instances
        ):  # type: int, Part, _InstanceCopy
            new_instances[index] = new_instance
            map_property_instances(
                original_part=i.instance_original, new_part=new_instance
            )

    if include_children:
        child_instances = []
        for i, new_instance in zip(instances, new_instances):
            child_models = {c.id: c for c in i.model_original.children()}

            for child_instance in i.instance_original.children():
                child_instances.append(
                    _InstanceCopy(
                        instance_original=child_instance,
                        model_original=child_models[child_instance.model_id],
                        target_parent_instance=new_instance,
                        name=child_instance.name,
                    )
                )

        _copy_instances_recursive(
            client=client,
            instances=child_instances,
            include_children=include_children,
        )

    return new_instances


def _update_references() -> None:
    """
    Set part reference values found when copying the Part(s).

    Part reference properties referring to child parts in the provided part tree should be updated to refer to
    the new child parts in the new tree. References to parts outside the provided tree can remain identical.
    Therefore, try to update the ID of the reference via the mapping dictionary.
    """
    mapping = get_mapping_dictionary()

    for (
        prop_original,
        references_original,
    ) in get_references().items():  # type: AnyProperty, List[Text]
        prop_new = mapping.get(prop_original.id)

        # Try to map to a new Part, default to the existing reference ID itself.
        references_new = [mapping.get(r, r) for r in references_original]
        if prop_new.type == PropertyType.REFERENCES_VALUE and references_new:

            if len(references_original) == 0:
                continue

            # Update the scope_id to match the new referenced part model
            # For parts copied in the same subtree
            if isinstance(references_new[0], Part):
                prop_new_options = {"scope_id": references_new[0].scope_id}
                prop_value = [ref.id for ref in references_new]
            # For parts left in the project from which they are copied from
            else:
                prop_value = list()
                for part_id in references_new:
                    referenced_part = prop_new._client.part(
                        pk=part_id, category=prop_new.category
                    )
                    prop_value.append(referenced_part.id)
                prop_new_options = {
                    "scope_id": prop_new._client.part(
                        pk=references_new[0], category=prop_new.category
                    ).scope_id
                }

            # Make sure the excluded property models ids are mapped on the new referenced part
            # model
            original_excluded_propmodel_ids = prop_original.get_excluded_propmodel_ids()
            if original_excluded_propmodel_ids:
                prop_new_options.update(
                    {
                        "propmodels_excl": [
                            mapping.get(r).id
                            for r in original_excluded_propmodel_ids
                            if r in mapping
                        ]
                    }
                )

            # Remap the prefilters on new referenced part model.
            original_prefilters = prop_original.get_prefilters()
            if original_prefilters:
                new_prefilters = [
                    PropertyValueFilter(
                        value=ovf.value,
                        filter_type=ovf.type,
                        property_model=mapping.get(ovf.id, ovf.id),
                    )
                    for ovf in original_prefilters
                ]
                prop_new_options.update(
                    PropertyValueFilter.write_options(filters=new_prefilters)
                )

            # Update the value and options (prefilters, excluded prop models and scope_id) in bulk
            if prop_new.category == Category.MODEL:
                prop_new.edit(value=prop_value, options=prop_new_options)
            else:
                prop_new.value = prop_value
        else:
            prop_new.value = references_new

    get_references(clean=True)


def _get_property_value(prop: AnyProperty) -> Any:
    """
    Get the property value, if directly applicable.

    In case of reference and attachment properties, the value has to be applied later via global attributes.

    :param prop: Any Property object
    :return: Any value
    """
    prop_value = None
    if prop.type in (
        PropertyType.REFERENCES_VALUE,
        PropertyType.ACTIVITY_REFERENCES_VALUE,
        PropertyType.SCOPE_REFERENCES_VALUE,
        PropertyType.TEAM_REFERENCES_VALUE,
        PropertyType.SERVICE_REFERENCES_VALUE,
    ):
        get_references()[prop] = prop.value_ids() if prop.has_value() else []
    elif prop.type == PropertyType.USER_REFERENCES_VALUE:
        get_references()[prop] = prop.value if prop.has_value() else []
    elif prop.type == PropertyType.ATTACHMENT_VALUE:
        get_attachments().append(prop)
    else:
        prop_value = prop._value

    return prop_value
