import datetime

import pytest

from pykechain.enums import Category, Classification, Multiplicity, PropertyType
from pykechain.exceptions import APIError, IllegalArgumentError, MultipleFoundError, NotFoundError
from pykechain.models import Part, PartSet
from tests.classes import TestBetamax


class TestParts(TestBetamax):
    def setUp(self):
        super().setUp()
        self._part = None

    def tearDown(self):
        if self._part:
            self._part.delete()
        super().tearDown()

    def test_retrieve_parts(self):
        parts = self.project.parts()

        # Check if there are parts
        self.assertTrue(len(parts))
        self.assertIsInstance(parts[0], Part)

    def test_retrieve_single_part(self):
        part_to_retrieve = self.project.parts()[0]
        part = self.project.part(part_to_retrieve.name)

        self.assertTrue(part)

    def test_base_comparison(self):
        all_parts = self.project.parts()

        tip = " See Base.__eq__() method."
        self.assertFalse(
            all_parts[0] == all_parts[1], msg="2 different parts must not be equal." + tip
        )
        self.assertTrue(all_parts[0] == all_parts[0], msg="The same part must be equal." + tip)
        self.assertFalse(
            all_parts[0] == 5, msg="A part must not be equal to a non-pykechain object." + tip
        )

    def test_base_hash(self):
        wheel = self.project.model("Wheel")
        a_dict = dict()

        try:
            a_dict[wheel] = 3
        except TypeError:
            self.assertTrue(False, msg="Parts must be hashable See Base.__hash__() method.")

    def test_part_attributes(self):
        attributes = [
            "_client",
            "_json_data",
            "id",
            "name",
            "created_at",
            "updated_at",
            "ref",
            "category",
            "classification",
            "parent_id",
            "description",
            "multiplicity",
            "_cached_children",
            "properties",
        ]

        obj = self.project.parts(limit=1)[0]
        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(
                    hasattr(obj, attribute),
                    "Could not find '{}' in the object: '{}'".format(
                        attribute, obj.__dict__.keys()
                    ),
                )

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.project.part("123lladadwd")

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.part()

    def test_retrieve_models(self):
        wheel = self.project.model("Wheel")

        self.assertTrue(self.project.parts(model=wheel))

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model("123lladadwd")

    def test_retrieve_model_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.model()

    def test_scope(self):
        first_part = self.project.parts()[0]

        self.assertEqual(first_part.scope(), self.project)

    def test_part_set_iterator(self):
        for part in self.project.parts():
            self.assertTrue(part.name)

    def test_part_set_get_item_invalid(self):
        part_set = self.project.parts()

        with self.assertRaises(NotImplementedError):
            # noinspection PyStatementEffect
            part_set["testing"]

    def test_wrongly_create_model(self):
        # setUp
        bike_model = self.project.model(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self.client.create_model(
                name="Multiplicity does not exist", parent=bike_model, multiplicity="TEN"
            )

    def test_part_add_delete_part(self):
        bike = self.project.part("Bike")
        wheel_model = self.project.model("Wheel")

        wheel = bike.add(wheel_model, name="Test Wheel")
        wheel.delete()

        wheel = wheel_model.add_to(bike)
        wheel.delete()

        with self.assertRaises(APIError):
            bike.delete()

    def test_create_part_where_parent_is_model(self):
        # setUp
        bike_model = self.project.model(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_part(
                name="Parent should be instance", parent=bike_model, model=bike_model
            )

    def test_create_part_where_model_is_instance(self):
        # setUp
        bike_instance = self.project.part(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_part(
                name="Model should not be instance", parent=bike_instance, model=bike_instance
            )

    def test_create_model_where_parent_is_instance(self):
        # setUp
        bike_instance = self.project.part(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_model(
                name="Parent should be model", parent=bike_instance, multiplicity=Multiplicity.ONE
            )

    def test_create_proxy_model_where_model_is_instance(self):
        # setUp
        bike_instance = self.project.part(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_proxy_model(
                name="Model should not be instance", model=bike_instance, parent=bike_instance
            )

    def test_create_proxy_model_where_parent_is_instance(self):
        # setUp
        bike_instance = self.project.part(name="Bike")
        bike_model = self.project.model(name="Bike")

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_proxy_model(
                name="Parent should not be instance", model=bike_model, parent=bike_instance
            )

    def test_add_to_wrong_categories(self):
        # This test has the purpose of testing of whether APIErrors are raised when illegal operations are
        # performed (e.g. operation that should be performed on part instances but instead are being performed
        # on part models and vice versa)
        project = self.project

        bike_model = project.model("Bike")
        bike_instance = project.part("Bike")
        wheel_model = project.model("Wheel")

        with self.assertRaises(APIError):
            self._part = bike_model.add(wheel_model)

        front_fork_instance = project.part("Front Fork")

        with self.assertRaises(APIError):
            self._part = front_fork_instance.add_to(bike_instance)

        with self.assertRaises(APIError):
            self._part = bike_instance.add_model("Engine")

        with self.assertRaises(APIError):
            self._part = bike_instance.add_property("Electrical Power")

        with self.assertRaises(APIError):
            self._part = bike_model.add_with_properties(wheel_model)

    def test_part_html_table(self):
        part = self.project.part("Front Wheel")

        self.assertIn("</table>", part._repr_html_())

    def test_part_set_html_table(self):
        parts = self.project.parts()

        self.assertIn("</table>", parts._repr_html_())

    def test_part_set_html_categories(self):
        parts = self.project.parts(category=None)

        self.assertIn("<th>Category</th>", parts._repr_html_())

    # version 1.1.2 and later
    def test_part_set_with_limit(self):
        limit = 5
        parts = self.project.parts(limit=limit)

        self.assertEqual(len(parts), limit)

    def test_part_set_with_batch(self):
        batch = 5
        parts = self.project.parts(batch=batch)
        self.assertTrue(len(parts) >= batch)

    # version 1.1.3 and later
    def test_retrieve_parent_of_part(self):
        frame = self.project.part("Frame")  # type: Part
        self.assertTrue(hasattr(frame, "parent_id"))
        parent_of_frame = frame.parent()
        self.assertIsInstance(parent_of_frame, type(frame))

    def test_retrieve_children_of_part(self):
        bike = self.project.part("Bike")  # type: Part
        self.assertIsInstance(bike, Part)
        children_of_bike = bike.children()
        self.assertIsInstance(children_of_bike, (PartSet, list))
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part("Frame")  # type: Part
        siblings_of_frame = frame.siblings()
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...

        # double check that the children of the parent of frame are the same as the siblings of frame
        children_of_parent_of_frame = frame.parent().children()  # type: PartSet
        self.assertEqual(len(children_of_parent_of_frame), len(siblings_of_frame))
        children_of_parent_of_frame_ids = [p.id for p in children_of_parent_of_frame]
        for sibling in siblings_of_frame:
            self.assertIn(
                sibling.id,
                children_of_parent_of_frame_ids,
                "sibling {} is appearing in the siblings method and not in the children of "
                "parent method".format(sibling),
            )

    # new in 1.3+
    def test_kwargs_on_part_retrieval(self):
        # test that the additional kwargs are added to the query filter on the api
        bikes = self.project.parts("Bike", order=True)  # type:PartSet
        self.assertTrue(len(bikes) == 1)
        self.assertTrue(self.client.last_url.find("order"))

    # new in 1.5+
    def test_edit_part_instance_name(self):
        front_fork = self.project.part("Front Fork")
        front_fork_old_name = str(front_fork.name)
        front_fork.edit(name="Front Fork - updated")

        front_fork_updated = self.project.part("Front Fork - updated")
        self.assertEqual(front_fork.id, front_fork_updated.id)
        self.assertEqual(front_fork.name, front_fork_updated.name)
        self.assertEqual(front_fork.name, "Front Fork - updated")

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(name=True)

        # teardown
        front_fork.edit(name=front_fork_old_name)

    def test_edit_part_instance_description(self):
        front_fork = self.project.part("Front Fork")
        front_fork_old_description = str(front_fork._json_data.get("description"))
        front_fork.edit(description="A normal Front Fork")

        front_fork_updated = self.project.part("Front Fork")
        self.assertEqual(front_fork.id, front_fork_updated.id)

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(description=42)

        # teardown
        front_fork.edit(description=front_fork_old_description)

    def test_edit_part_model_name(self):
        front_fork = self.project.model("Front Fork")
        front_fork_oldname = str(front_fork.name)
        front_fork.edit(name="Front Fork - updated")

        front_fork_updated = self.project.model("Front Fork - updated")
        self.assertEqual(front_fork.id, front_fork_updated.id)
        self.assertEqual(front_fork.name, front_fork_updated.name)

        # teardown
        front_fork.edit(name=front_fork_oldname)

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_part_clear_values(self):
        # setup
        front_fork = self.project.part("Front Fork")
        front_fork_name = str(front_fork.name)
        front_fork_description = str(front_fork.description)

        front_fork.edit(name=None, description=None)

        # testing
        self.assertEqual(front_fork.name, front_fork_name)
        self.assertEqual(front_fork.description, "")

        # tearDown
        front_fork.edit(description=front_fork_description)

    def test_create_model(self):
        bike = self.project.model("Bike")
        pedal = self.project.create_model(bike, "Pedal", multiplicity=Multiplicity.ONE)
        self._part = pedal
        pedal_model = self.project.model("Pedal")

        self.assertTrue(pedal.id, pedal_model.id)
        self.assertTrue(pedal._json_data["multiplicity"], "ONE")

    def test_add_proxy_to(self):
        catalog_container = self.project.model(name__startswith="Catalog")
        bearing_catalog_model = catalog_container.add_model(
            "Bearing", multiplicity=Multiplicity.ZERO_MANY
        )
        wheel_model = self.project.model("Wheel")

        bearing_proxy_model = bearing_catalog_model.add_proxy_to(
            wheel_model, "Bearing", Multiplicity.ZERO_ONE
        )

        self.assertTrue(bearing_proxy_model.category, Category.MODEL)
        self.assertTrue(bearing_proxy_model.parent(), wheel_model)

        # teardown
        all_bearing_proxies = self.project.parts(
            name="Bearing", category=Category.MODEL, parent=wheel_model.id
        )
        self.assertGreaterEqual(len(all_bearing_proxies), 1)
        for bearing_proxy in all_bearing_proxies:
            bearing_proxy.delete()

        all_bearing_catalog_models = self.project.parts(name="Bearing", category=Category.MODEL)
        self.assertGreaterEqual(len(all_bearing_catalog_models), 1)
        for bearing_catalog_model in all_bearing_catalog_models:
            bearing_catalog_model.delete()

        all_bearing_models = self.project.parts(name="Bearing", category=Category.MODEL)
        self.assertEqual(len(all_bearing_models), 0)

    # new in 1.6
    def test_retrieve_model(self):
        front_fork = self.project.part("Front Fork")
        front_fork_model = self.project.model("Front Fork")

        front_fork_retrieved_model = front_fork.model()

        # Added to improve coverage. Assert whether NotFoundError is raised when model() method is applied to
        # a part that has no model
        with self.assertRaises(NotFoundError):
            front_fork_model.model()

        self.assertEqual(front_fork_model.id, front_fork_retrieved_model.id)

    def test_count_instances(self):
        front_fork_model = self.project.model("Wheel")
        nr = front_fork_model.count_instances()

        self.assertIsInstance(nr, int)
        self.assertEqual(2, nr)

        bike_part = self.project.part("Bike")
        with self.assertRaises(IllegalArgumentError):
            bike_part.count_instances()

    def test_count_children(self):
        bike_instance = self.project.part("Bike")
        bike_model = self.project.model("Bike")

        nr = bike_instance.count_children()

        self.assertIsInstance(nr, int)
        self.assertEqual(7, nr)

        nr = bike_model.count_children()

        self.assertEqual(5, nr)

        nr = bike_instance.count_children(name__contains="Wheel")

        self.assertEqual(2, nr)

    def test_retrieve_catalog_model_of_proxy(self):
        catalog_container = self.project.model(name__startswith="Catalog")
        bearing_catalog_model = catalog_container.add_model(
            "Bearing", multiplicity=Multiplicity.ZERO_MANY
        )
        wheel_model = self.project.model("Wheel")

        # add proxy model to product Bike > Wheel based on catalog model 'Bearing'
        bearing_proxy_model = bearing_catalog_model.add_proxy_to(
            wheel_model, "Bearing", Multiplicity.ZERO_ONE
        )

        self.assertTrue(bearing_proxy_model.category, Category.MODEL)
        self.assertTrue(bearing_proxy_model.parent(), wheel_model)

        # the call to test here
        re_retrieved_bearing_catalog_model = self.project.model(
            "Bearing", classification=Classification.CATALOG
        )
        self.assertEqual(bearing_catalog_model, re_retrieved_bearing_catalog_model)

        # teardown
        all_bearing_proxies = self.project.parts(
            name="Bearing", category=Category.MODEL, parent=wheel_model.id
        )
        self.assertGreaterEqual(len(all_bearing_proxies), 1)
        for bearing_proxy in all_bearing_proxies:
            bearing_proxy.delete()

        all_bearing_catalog_models = self.project.parts(name="Bearing", category=Category.MODEL)
        self.assertGreaterEqual(len(all_bearing_catalog_models), 1)
        for bearing_catalog_model in all_bearing_catalog_models:
            bearing_catalog_model.delete()

        all_bearing_models = self.project.parts(name="Bearing", category=Category.MODEL)
        self.assertEqual(len(all_bearing_models), 0)

    def test_retrieve_non_existent_proxies_of_a_catalog_model_raises_error(self):
        # Added to improve coverage. Assert whether NotFoundError is raised when proxy_model() method is applied to
        # a part that is not a proxy
        catalog_model = self.project.model("Model", classification=Classification.CATALOG)
        with self.assertRaises(NotFoundError):
            catalog_model.proxy_model()

    def test_retrieve_proxy_of_instance(self):
        instance = self.project.part("Rear Wheel")

        with self.assertRaises(IllegalArgumentError):
            instance.proxy_model()

    # new in 1.8+
    def test_retrieve_part_multiplicity(self):
        bike_model = self.project.model("Bike")
        self.assertEqual(bike_model.multiplicity, Multiplicity.ONE_MANY, bike_model.multiplicity)

    # new in 1.9
    def test_retrieve_part_properties_in_a_dict(self):
        # Retrieve the bike part
        bike = self.project.part("Bike")

        # Call the function to be tested
        bike_properties = bike.as_dict()

        # Check whether bike_properties contains all the property names in bike
        for prop in bike.properties:
            self.assertTrue(prop.name in bike_properties)

    # new in 1.12
    def test_retrieve_children_of_part_with_additional_arguments(self):
        bike = self.project.part("Bike")  # type: Part
        self.assertIsInstance(bike, Part)
        children_of_bike = bike.children(name__icontains="Wheel")
        self.assertIsInstance(children_of_bike, PartSet)
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part_with_additional_arguments(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part("Frame")  # type: Part
        siblings_of_frame = frame.siblings(name__icontains="Wheel")
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...

    # new in 2.3
    def test_clone_model(self):
        # setUp
        model_name = "Seat"
        seat = self.project.model(model_name)
        self._part = seat.clone()

        # testing
        clone_seat_model = self.project.model(f"CLONE - {model_name}")
        self.assertTrue(clone_seat_model)

    def test_clone_instance(self):
        instance_name = "Front Wheel"
        wheel = self.project.part(instance_name)
        self._part = wheel.clone()

        # testing
        clone_spoke_instance = self.project.part(f"CLONE - {instance_name}")
        self.assertTrue(clone_spoke_instance)

    def test_clone_instance_with_multiplicity_violation(self):
        instance_name = "Seat"
        seat = self.project.part(instance_name)

        seat_model = seat.model()

        # testing
        self.assertEqual(Multiplicity.ONE, seat_model.multiplicity)
        with self.assertRaises(APIError):
            self._part = seat.clone()


@pytest.mark.skipif(
    "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
)
class TestBulkPartsCreation(TestBetamax):
    def setUp(self):
        super().setUp()

        self.product_model = self.project.model(name="Product")
        self.part_model = self.project.create_model(name="Part", parent=self.product_model)
        self.text_prop = self.part_model.add_property(
            name="Text Property", property_type=PropertyType.TEXT_VALUE, unit="mm"
        )
        self.char_prop = self.part_model.add_property(
            name="Char Property", property_type=PropertyType.CHAR_VALUE
        )
        self.int_prop = self.part_model.add_property(
            name="Int Property", property_type=PropertyType.INT_VALUE
        )
        self.float_prop = self.part_model.add_property(
            name="Float Property", property_type=PropertyType.FLOAT_VALUE
        )
        self.bool_prop = self.part_model.add_property(
            name="Boolean Property", property_type=PropertyType.BOOLEAN_VALUE
        )
        self.date_prop = self.part_model.add_property(
            name="Date Property", property_type=PropertyType.DATE_VALUE
        )
        self.datetime_prop = self.part_model.add_property(
            name="Datetime Property", property_type=PropertyType.DATETIME_VALUE
        )
        self.attachment_prop = self.part_model.add_property(
            name="Attach Property", property_type=PropertyType.ATTACHMENT_VALUE
        )
        self.link_prop = self.part_model.add_property(
            name="Link Property", property_type=PropertyType.LINK_VALUE
        )
        self.ss_prop = self.part_model.add_property(
            name="SS Property", property_type=PropertyType.SINGLE_SELECT_VALUE
        )
        self.ss_prop.options = ["1", "2", "3", "4", "5"]
        self.ms_prop = self.part_model.add_property(
            name="MS Property",
            property_type=PropertyType.MULTI_SELECT_VALUE,
            options={"value_choices": ["1", "2", "3", "4", "5"]},
        )
        self.part_ref_prop = self.part_model.add_property(
            name="Part ref Property",
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.project.model(name="Wheel").id,
        )
        self.geo_info_prop = self.part_model.add_property(
            name="Geo Property", property_type=PropertyType.GEOJSON_VALUE
        )
        self.weather_prop = self.part_model.add_property(
            name="Weather Property", property_type=PropertyType.WEATHER_VALUE
        )
        self.act_ref_prop = self.part_model.add_property(
            name="Act Property", property_type=PropertyType.ACTIVITY_REFERENCES_VALUE
        )

        self.product_part = self.project.part(name="Product")
        self.part_dict = {
            "name": "Dummy name",
            "parent_id": self.product_part.id,
            "description": "",
            "model_id": self.part_model.id,
            "properties": [
                {
                    "name": self.text_prop.name,
                    "value": "Dummy value",
                    "model_id": self.text_prop.id,
                }
            ],
        }

    def tearDown(self):
        self.part_model.delete()

    """Bulk parts creation"""

    def test_bulk_create_parts(self):
        new_parts = list()
        for idx in range(1, 5):
            part_dict = {
                "name": idx,
                "parent_id": self.product_part.id,
                "description": f"Description part {idx}",
                "model_id": self.part_model.id,
                "properties": [
                    {
                        "name": self.text_prop.name,
                        "value": f"{idx}",
                        "model_id": self.text_prop.id,
                    },
                    {
                        "name": self.char_prop.name,
                        "value": f"{idx}",
                        "model_id": self.char_prop.id,
                    },
                    {"name": self.int_prop.name, "value": idx, "model_id": self.int_prop.id},
                    {
                        "name": self.float_prop.name,
                        "value": float(f"{idx}.{idx}"),
                        "model_id": self.float_prop.id,
                    },
                    {
                        "name": self.bool_prop.name,
                        "value": True if idx % 2 == 0 else False,
                        "model_id": self.bool_prop.id,
                    },
                    {
                        "name": self.date_prop.name,
                        "value": datetime.date(2020, idx, idx).isoformat(),
                        "model_id": self.date_prop.id,
                    },
                    {
                        "name": self.datetime_prop.name,
                        "value": datetime.datetime(2020, idx, idx, 15, 00, 00).isoformat("T"),
                        "model_id": self.datetime_prop.id,
                    },
                    {
                        "name": self.link_prop.name,
                        "value": f"http://{idx}.com",
                        "model_id": self.link_prop.id,
                    },
                    {"name": self.ss_prop.name, "value": f"{idx}", "model_id": self.ss_prop.id},
                    {"name": self.ms_prop.name, "value": [f"{idx}"], "model_id": self.ms_prop.id},
                    {
                        "name": self.part_ref_prop.name,
                        "value": [self.project.part(name="Front Wheel").id],
                        "model_id": self.part_ref_prop.id,
                    },
                    {
                        "name": self.act_ref_prop.name,
                        "value": [self.project.activity(name="Specify wheel diameter").id],
                        "model_id": self.act_ref_prop.id,
                    },
                ],
            }
            new_parts.append(part_dict)
        parts_created = self.client._create_parts_bulk(parts=new_parts)

        # testing
        self.assertEqual(len(parts_created), 4)
        for part_created in parts_created:
            idx = int(part_created.name)
            self.assertEqual(part_created.description, f"Description part {idx}")
            self.assertEqual(part_created.category, Category.INSTANCE)
            self.assertEqual(len(part_created.properties), 15)

            self.assertEqual(part_created.property(name=self.text_prop.name).value, str(idx))
            self.assertEqual(part_created.property(name=self.char_prop.name).value, str(idx))
            self.assertEqual(part_created.property(name=self.int_prop.name).value, idx)
            self.assertEqual(
                part_created.property(name=self.float_prop.name).value, float(f"{idx}.{idx}")
            )
            self.assertEqual(
                part_created.property(name=self.bool_prop.name).value,
                True if idx % 2 == 0 else False,
            )
            self.assertEqual(
                part_created.property(name=self.date_prop.name).value,
                datetime.date(2020, idx, idx).isoformat(),
            )
            self.assertEqual(
                part_created.property(name=self.datetime_prop.name).value.split("+")[0],
                datetime.datetime(2020, idx, idx, 15, 00, 00).isoformat("T"),
            )
            self.assertEqual(
                part_created.property(name=self.link_prop.name).value, f"http://{idx}.com"
            )
            self.assertEqual(part_created.property(name=self.ss_prop.name).value, f"{idx}")
            self.assertEqual(part_created.property(name=self.ms_prop.name).value, [f"{idx}"])
            self.assertEqual(
                part_created.property(name=self.part_ref_prop.name).value[0].name, "Front Wheel"
            )
            self.assertEqual(
                part_created.property(name=self.act_ref_prop.name).value[0].name,
                "Specify wheel diameter",
            )
            self.assertEqual(part_created.property(name=self.weather_prop.name).value, dict())
            self.assertEqual(part_created.property(name=self.geo_info_prop.name).value, dict())

    def test_bulk_create_parts_without_name(self):
        self.part_dict.pop("name")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_parent_id(self):
        self.part_dict.pop("parent_id")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_model_id(self):
        self.part_dict.pop("model_id")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_properties(self):
        self.part_dict.pop("properties")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_property_name(self):
        self.part_dict["properties"][0].pop("name")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_property_model_id(self):
        self.part_dict["properties"][0].pop("model_id")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])

    def test_bulk_create_parts_without_property_value(self):
        self.part_dict["properties"][0].pop("value")
        with self.assertRaises(IllegalArgumentError):
            self.client._create_parts_bulk(parts=[self.part_dict])


@pytest.mark.skipif(
    "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
)
class TestBulkPartsDeletion(TestBetamax):
    def setUp(self):
        super().setUp()
        self.parts = list()
        self.wheel_model = self.project.model(name="Wheel")
        self.bike_instance = self.project.part(name="Bike")

        self.diameter_prop = self.wheel_model.property(name="Diameter")
        self.spokes_prop = self.wheel_model.property(name="Spokes")
        self.rim_material_prop = self.wheel_model.property(name="Rim Material")
        self.tire_thickness_prop = self.wheel_model.property(name="Tire Thickness")

        for idx in range(1, 5):
            part_dict = {
                "name": f"Wheel {idx}",
                "parent_id": self.bike_instance.id,
                "description": "",
                "model_id": self.wheel_model.id,
                "properties": [
                    {
                        "name": self.diameter_prop.name,
                        "value": float(f"{idx}.{idx}"),
                        "model_id": self.diameter_prop.id,
                    },
                    {
                        "name": self.spokes_prop.name,
                        "value": f"{idx}",
                        "model_id": self.spokes_prop.id,
                    },
                    {
                        "name": self.rim_material_prop.name,
                        "value": f"Material {idx}",
                        "model_id": self.rim_material_prop.id,
                    },
                    {
                        "name": self.tire_thickness_prop.name,
                        "value": float(f"{idx}.{idx}"),
                        "model_id": self.tire_thickness_prop.id,
                    },
                ],
            }
            self.parts.append(part_dict)
        self.parts_created = list(self.client._create_parts_bulk(parts=self.parts))

    def tearDown(self):
        for part in self.parts_created:
            # In case the parts have not been deleted and a clean up is required
            try:
                part.delete()
            except APIError:
                pass

    def test_bulk_delete_parts(self):
        input_parts_and_uuids = [
            self.parts_created[0],
            self.parts_created[1],
            self.parts_created[2].id,
            self.parts_created[3].id,
        ]
        self.client._delete_parts_bulk(parts=input_parts_and_uuids)
        for idx in range(1, 5):
            with self.subTest(idx=idx):
                with self.assertRaises(NotFoundError):
                    self.project.part(name=f"Wheel {idx}")

    def test_bulk_delete_parts_with_wrong_input(self):
        wrong_input = [self.project.activity(name="Specify wheel diameter")]
        with self.assertRaises(IllegalArgumentError):
            self.client._delete_parts_bulk(parts=wrong_input)

class TestPartsClassificationForm(TestBetamax):
    def setUp(self):
        super().setUp()
        self._part = None

    def tearDown(self):
        if self._part:
            self._part.delete()
        super().tearDown()

    def test_classification_forms_exist(self):
        parts = self.project.parts(category=None, classification=Classification.FORM)

        for p in parts:
            self.assertEqual(p.classification, Classification.FORM)
            parent = p.parent()
            if parent.name == "Root":
                self.assertEqual(parent.classification, "ROOT")
            else:
                self.assertEqual(parent.classification, Classification.FORM)
