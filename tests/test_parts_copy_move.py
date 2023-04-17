import os
from datetime import datetime, date, time, timezone

from pykechain.enums import FilterType, Multiplicity, PropertyType, ScopeStatus
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models.value_filter import ScopeFilter
from tests.classes import TestBetamax


class TestPartsCopyMove(TestBetamax):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"))

    def setUp(self):
        super().setUp()
        self.base = self.project.model(name__startswith="Catalog")
        self.cross_scope_project = self.client.scope(ref="cannondale-project")
        self.cross_scope_bike = self.cross_scope_project.model(ref="cannondale-bike")
        self.wheel = self.project.model(name="Wheel")
        self.front_wheel, self.rear_wheel = self.project.part(
            name="Front Wheel"
        ), self.project.part(name="Rear Wheel")
        self.specify_wheel_diameter = self.project.activity(name="Specify wheel diameter")
        self.model_to_be_copied = self.project.create_model(
            parent=self.base,
            name=f"__Model to be Copied @ {str(datetime.now())} [TEST]",
            multiplicity=Multiplicity.ONE_MANY,
        )  # type Part
        self.p_char_name = "__Property single text"
        self.p_multi_name = "__Property multi text"
        self.p_bool_name = "__Property boolean"
        self.p_int_name = "__Property integer"
        self.p_float_name = "__Property float"
        self.p_date_name = "__Property date"
        self.p_datetime_name = "__Property datetime"
        self.p_time_name = "__Property time"
        self.p_attach_name = "__Property attachment"
        self.p_link_name = "__Property link"
        self.p_single_select_name = "__Property single select"
        self.p_multi_select_name = "__Property multi select"
        self.p_part_reference_name = "__Property part reference"
        self.p_part_reference_name_cross_scope = "__Property part reference cross scope"
        self.p_geo_json_name = "__Property geographical"
        self.p_weather_name = "__Property weather"
        self.p_activity_reference_name = "__Property activity reference"
        self.p_user_reference_name = "__Property user reference"
        self.p_project_reference_name = "__Property project reference"
        self.p_char_value = "test value"
        self.p_multi_value = "test multi text value"
        self.p_bool_value = True
        self.p_int_value = 33
        self.p_float_value = 42.42
        self.p_date_value = str(date(2021, 12, 15))
        self.p_datetime_value = str(datetime(1991, 4, 12, 13, 5, 5).isoformat())
        self.p_time_value = str(time(12, 0, 4))
        self.p_attach_value = self.project_root + "/requirements.txt"
        self.p_link_value = "http://ke-chain.com"
        self.p_select_value_choices = ["apples", "oranges", "bananas", "lemons"]
        self.p_single_select_value = "bananas"
        self.p_multi_select_value = ["apples", "bananas"]
        self.test_manager = self.client.user(username="testmanager")
        self.test_supervisor = self.client.user(username="testsupervisor")
        self.p_user_reference_value = [self.test_manager.id, self.test_supervisor.id]
        self.p_geojson_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [4.390912, 51.9929856]},
                    "properties": {
                        "zoom": 16,
                        "address": "Rijksstraatweg 47, 2645 BS Delfgauw, Netherlands",
                    },
                }
            ],
        }
        self.p_geojson_value_options = {
            "representations": [
                {"rtype": "geoCoordinate", "config": {"geoCoordinate": "approx_address"}}
            ]
        }
        self.p_weather_value = {
            "current": {
                "uv": 1,
                "cloud": 0,
                "is_day": 1,
                "temp_c": 12,
                "temp_f": 53.6,
                "vis_km": 10,
                "gust_kph": 11.2,
                "gust_mph": 6.9,
                "humidity": 88,
                "wind_dir": "NE",
                "wind_kph": 0,
                "wind_mph": 0,
                "condition": {
                    "code": 1000,
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                    "text": "Sunny",
                },
                "precip_in": 0,
                "precip_mm": 0,
                "vis_miles": 6,
                "feelslike_c": 11.9,
                "feelslike_f": 53.5,
                "pressure_in": 30.42,
                "pressure_mb": 1030,
                "wind_degree": 52,
                "last_updated": "2021-09-21 09:30",
                "last_updated_epoch": 1632209400,
            },
            "location": {
                "lat": 51.99,
                "lon": 4.39,
                "name": "Delfgauw",
                "tz_id": "Europe/Amsterdam",
                "region": "South Holland",
                "country": "Netherlands",
                "localtime": "2021-09-21 9:39",
                "localtime_epoch": 1632209956,
            },
        }
        self.sub_part1 = self.model_to_be_copied.add_model(
            name="__subpart 1", multiplicity=Multiplicity.ONE
        )
        self.sub_part2 = self.model_to_be_copied.add_model(
            name="__subpart 2", multiplicity=Multiplicity.ZERO_MANY
        )
        self.model_to_be_copied.add_property(
            name=self.p_char_name,
            description="Description of Property single text",
            unit="mm",
            default_value=self.p_char_value,
            property_type=PropertyType.CHAR_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_multi_name,
            unit="mm",
            default_value=self.p_multi_value,
            property_type=PropertyType.TEXT_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_bool_name,
            default_value=self.p_bool_value,
            property_type=PropertyType.BOOLEAN_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_int_name,
            default_value=self.p_int_value,
            property_type=PropertyType.INT_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_float_name,
            default_value=self.p_float_value,
            property_type=PropertyType.FLOAT_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_date_name,
            default_value=self.p_date_value,
            property_type=PropertyType.DATE_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_datetime_name,
            default_value=self.p_datetime_value,
            property_type=PropertyType.DATETIME_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_time_name,
            default_value=self.p_time_value,
            property_type=PropertyType.TIME_VALUE,
        )
        self.attachment_property = self.model_to_be_copied.add_property(
            name=self.p_attach_name, property_type=PropertyType.ATTACHMENT_VALUE
        )
        self.attachment_property.upload(self.p_attach_value)

        self.model_to_be_copied.add_property(
            name=self.p_link_name,
            default_value=self.p_link_value,
            property_type=PropertyType.LINK_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_single_select_name,
            options=dict(value_choices=self.p_select_value_choices),
            default_value=self.p_single_select_value,
            property_type=PropertyType.SINGLE_SELECT_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_multi_select_name,
            default_value=self.p_multi_select_value,
            options=dict(value_choices=self.p_select_value_choices),
            property_type=PropertyType.MULTI_SELECT_VALUE,
        )
        self.model_to_be_copied.add_property(
            name=self.p_part_reference_name,
            default_value=self.sub_part2,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.ref_property = self.model_to_be_copied.add_property(
            name=self.p_part_reference_name_cross_scope,
            default_value=self.wheel,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.ref_property.set_prefilters(
            property_models=[self.wheel.property(name="Rim Material"),
                             self.wheel.property(name="Country of manufacture")],
            values=['Aliminium', 'United States'],
            filters_type=[FilterType.CONTAINS, FilterType.CONTAINS],
        )
        self.model_to_be_copied.add_property(
            name=self.p_geo_json_name,
            property_type=PropertyType.GEOJSON_VALUE,
            default_value=self.p_geojson_value,
            value_options=self.p_geojson_value_options,
        )
        self.model_to_be_copied.add_property(
            name=self.p_weather_name,
            property_type=PropertyType.WEATHER_VALUE,
            default_value=self.p_weather_value,
        )
        self.model_to_be_copied.add_property(
            name=self.p_activity_reference_name,
            property_type=PropertyType.ACTIVITY_REFERENCES_VALUE,
            default_value=[self.specify_wheel_diameter.id],
        )
        self.model_to_be_copied.add_property(
            name=self.p_user_reference_name,
            property_type=PropertyType.USER_REFERENCES_VALUE,
            default_value=self.p_user_reference_value,
        )
        self.model_to_be_copied.add_property(
            name=self.p_project_reference_name,
            property_type=PropertyType.SCOPE_REFERENCES_VALUE,
            default_value=[self.project.id],
        )
        self.sub_part2.add_property(
            name=self.p_bool_name,
            default_value=False,
            property_type=PropertyType.BOOLEAN_VALUE,
        )
        self.sub_part2.add_property(
            name=self.p_int_name,
            default_value=3,
            property_type=PropertyType.INT_VALUE,
        )

        self.model_to_be_copied.property(self.p_part_reference_name).set_excluded_propmodels(
            [self.sub_part2.property(self.p_bool_name)]
        )
        self.model_to_be_copied.property(self.p_part_reference_name).set_prefilters(
            property_models=[self.sub_part2.property(self.p_int_name)],
            values=[3],
            filters_type=[FilterType.GREATER_THAN_EQUAL],
        )
        self.model_to_be_copied.property(self.p_project_reference_name).set_prefilters(
            [ScopeFilter(tag='bike'), ScopeFilter(status=ScopeStatus.ACTIVE)]
        )

        self.model_target_parent = self.project.model(ref="bike")
        self.instance_to_be_copied = self.model_to_be_copied.instances()[0]
        self.sub_part2_instance = self.instance_to_be_copied.add(model=self.sub_part2)
        self.instance_to_be_copied.property(name=self.p_part_reference_name).value = [
            self.sub_part2_instance
        ]
        self.instance_to_be_copied.property(name=self.p_part_reference_name_cross_scope).value = [
            self.front_wheel
        ]
        self.instance_target_parent = self.model_to_be_copied.parent().instances()[0]
        self.dump_part = None

    def tearDown(self):
        self.model_to_be_copied.delete()

        if self.dump_part:
            self.dump_part.delete()
        super().tearDown()

    def test_copy_part_model_given_name_include_children(self):
        model_target_parent = self.project.model("Bike")
        copied_model = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name="__Copied model under Bike",
            include_children=True,
            include_instances=False,
        )
        copied_model.refresh()
        copied_model.populate_descendants()
        self.dump_part = copied_model

        # testing
        self.assertTrue(copied_model)
        self.assertEqual(len(copied_model.properties), len(self.model_to_be_copied.properties))
        self.assertEqual(
            copied_model.property(name=self.p_char_name)._json_data["description"],
            "Description of Property single text",
        )
        self.assertEqual(copied_model.property(name=self.p_char_name)._json_data["unit"], "mm")
        self.assertEqual(copied_model.property(name=self.p_int_name).value, self.p_int_value)
        self.assertEqual(copied_model.property(name=self.p_char_name).value, self.p_char_value)
        self.assertEqual(copied_model.property(name=self.p_multi_name).value, self.p_multi_value)
        self.assertEqual(copied_model.property(name=self.p_int_name).value, self.p_int_value)
        self.assertEqual(copied_model.property(name=self.p_float_name).value, self.p_float_value)
        self.assertEqual(copied_model.property(name=self.p_bool_name).value, self.p_bool_value)
        self.assertEqual(copied_model.property(name=self.p_date_name).value, self.p_date_value)
        self.assertIn(
            self.p_datetime_value, copied_model.property(name=self.p_datetime_name).value
        )
        self.assertIn(copied_model.property(name=self.p_attach_name).filename, self.p_attach_value)
        self.assertEqual(copied_model.property(name=self.p_link_name).value, self.p_link_value)
        self.assertEqual(
            copied_model.property(name=self.p_single_select_name).value, self.p_single_select_value
        )
        self.assertEqual(
            copied_model.property(name=self.p_multi_select_name).value, self.p_multi_select_value
        )
        list_of_user_ids = [
            user.id for user in copied_model.property(name=self.p_user_reference_name).value
        ]
        self.assertIn(
            self.sub_part2.name,
            [part.name for part in copied_model.property(name=self.p_part_reference_name).value],
        )
        self.assertNotEqual(
            self.sub_part2.id, copied_model.property(name=self.p_part_reference_name).value[0].id
        )
        self.assertIn(
            self.wheel.id,
            [
                part.id
                for part in copied_model.property(
                    name=self.p_part_reference_name_cross_scope
                ).value
            ],
        )
        self.assertDictEqual(
            self.p_geojson_value, copied_model.property(name=self.p_geo_json_name).value
        )
        self.assertDictEqual(
            self.p_weather_value, copied_model.property(name=self.p_weather_name).value
        )
        self.assertIn(
            self.specify_wheel_diameter.id,
            [act.id for act in copied_model.property(name=self.p_activity_reference_name).value],
        )
        self.assertIn(
            self.project.id,
            [
                scope.id
                for scope in copied_model.property(name=self.p_project_reference_name).value
            ],
        )
        self.assertIn(self.test_manager.id, list_of_user_ids)
        self.assertIn(self.test_supervisor.id, list_of_user_ids)
        self.assertEqual(
            copied_model.property(name=self.p_single_select_name).options,
            self.p_select_value_choices,
        )
        self.assertEqual(
            copied_model.property(name=self.p_multi_select_name).options,
            self.p_select_value_choices,
        )
        self.assertEqual(len(copied_model._cached_children), 2)

    def test_copy_part_model_include_instances(self):
        model_target_parent = self.project.model("Bike")
        self.dump_part = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name="__Copied model under Bike",
            include_children=True,
            include_instances=True,
        )
        bike_part = self.project.part("Bike")

        copied_instance = [child for child in bike_part.children() if "Copied" in child.name][0]
        copied_instance.populate_descendants()

        # testing
        self.assertTrue(copied_instance)
        self.assertEqual(len(copied_instance.properties), len(self.model_to_be_copied.properties))
        self.assertEqual(copied_instance.property(name=self.p_char_name).value, self.p_char_value)
        self.assertEqual(
            copied_instance.property(name=self.p_multi_name).value, self.p_multi_value
        )
        self.assertEqual(copied_instance.property(name=self.p_int_name).value, self.p_int_value)
        self.assertEqual(
            copied_instance.property(name=self.p_float_name).value, self.p_float_value
        )
        self.assertEqual(copied_instance.property(name=self.p_bool_name).value, self.p_bool_value)
        self.assertEqual(copied_instance.property(name=self.p_date_name).value, self.p_date_value)
        self.assertIn(
            self.p_datetime_value, copied_instance.property(name=self.p_datetime_name).value
        )
        self.assertEqual(copied_instance.property(name=self.p_link_name).value, self.p_link_value)
        self.assertEqual(
            copied_instance.property(name=self.p_single_select_name).value,
            self.p_single_select_value,
        )
        self.assertEqual(
            copied_instance.property(name=self.p_multi_select_name).value,
            self.p_multi_select_value,
        )
        list_of_user_ids = [
            user.id for user in copied_instance.property(name=self.p_user_reference_name).value
        ]
        self.assertIn(
            self.sub_part2.name,
            [
                part.name
                for part in copied_instance.property(name=self.p_part_reference_name).value
            ],
        )
        self.assertNotEqual(
            self.sub_part2.id,
            copied_instance.property(name=self.p_part_reference_name).value[0].id,
        )
        self.assertIn(
            self.front_wheel.id,
            [
                part.id
                for part in copied_instance.property(
                    name=self.p_part_reference_name_cross_scope
                ).value
            ],
        )
        self.assertDictEqual(
            self.p_geojson_value, copied_instance.property(name=self.p_geo_json_name).value
        )
        self.assertDictEqual(
            self.p_weather_value, copied_instance.property(name=self.p_weather_name).value
        )
        self.assertIn(
            self.specify_wheel_diameter.id,
            [
                act.id
                for act in copied_instance.property(name=self.p_activity_reference_name).value
            ],
        )
        self.assertIn(
            self.project.id,
            [
                scope.id
                for scope in copied_instance.property(name=self.p_project_reference_name).value
            ],
        )
        self.assertIn(self.test_manager.id, list_of_user_ids)
        self.assertIn(self.test_supervisor.id, list_of_user_ids)

        self.assertEqual(len(copied_instance._cached_children), 2)

    def test_copy_part_model_empty_name_not_include_children(self):
        # setUp
        model_target_parent = self.project.model("Bike")
        name_of_part = "__Copied model under Bike"
        copied_model = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name=name_of_part,
            include_children=False,
            include_instances=False,
        )

        copied_model.populate_descendants()
        self.dump_part = copied_model

        # testing
        self.assertTrue(copied_model)
        self.assertEqual(copied_model.name, name_of_part)
        self.assertEqual(len(copied_model.properties), len(self.model_to_be_copied.properties))
        self.assertEqual(len(copied_model._cached_children), 0)

    def test_copy_internal_references_on_model(self):
        child_model = self.model_to_be_copied.children()[0]
        self.model_to_be_copied.add_property(
            name="__Property internal reference",
            default_value=child_model,
            property_type=PropertyType.REFERENCES_VALUE,
        )

        model_target_parent = self.project.model("Bike")
        self.dump_part = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name="__Copied model under Bike",
            include_children=True,
            include_instances=False,
        )

        self.dump_part.refresh()
        copied_child = self.dump_part.children()[0]
        reference_property = self.dump_part.property(name="__Property internal reference")

        self.assertEqual(copied_child, reference_property.value[0])

    def test_copy_internal_references_on_instance(self):
        prop_name = "__Property internal reference"
        child_model = self.model_to_be_copied.children()[0]
        self.model_to_be_copied.add_property(
            name=prop_name, default_value=child_model, property_type=PropertyType.REFERENCES_VALUE
        )

        self.instance_to_be_copied.refresh()  # to load the new property
        self.instance_to_be_copied.property(
            name=prop_name
        ).value = self.instance_to_be_copied.children()[0]

        instance_target_parent = self.project.part("Bike")
        copied_instance = self.instance_to_be_copied.copy(
            target_parent=instance_target_parent,
            name="__Copied instance under Bike",
            include_children=True,
        )
        self.dump_part = copied_instance.model()

        copied_child = copied_instance.children()[0]
        reference_property = copied_instance.property(name=prop_name)

        self.assertTrue(reference_property.has_value())
        self.assertEqual(copied_child, reference_property.value[0])

    def test_move_part_model(self):
        # setUp
        model_target_parent = self.project.model("Bike")
        original_model_to_be_copied_name = self.model_to_be_copied.name
        self.model_to_be_copied = self.model_to_be_copied.move(
            target_parent=model_target_parent, name="__New part under bike", include_children=True
        )

        # testing
        with self.assertRaises(NotFoundError):
            self.project.model(name=original_model_to_be_copied_name)

    def test_copy_part_instance(self):
        # setUp
        instance_to_be_copied = self.model_to_be_copied.instances()[0]
        instance_to_be_copied.property(name=self.p_attach_name).upload(self.p_attach_value)
        instance_to_be_copied.property(name=self.p_part_reference_name_cross_scope).value = [
            self.front_wheel,
            self.rear_wheel,
        ]

        instance_target_parent = self.project.part("Bike")
        copied_instance = instance_to_be_copied.copy(
            target_parent=instance_target_parent, name="__Copied instance", include_children=True
        )
        copied_instance.populate_descendants()
        self.dump_part = copied_instance.model()

        # testing
        self.assertTrue(copied_instance)
        self.assertEqual(copied_instance.name, "__Copied instance")
        self.assertEqual(len(copied_instance.properties), len(self.model_to_be_copied.properties))
        self.assertEqual(copied_instance.property(name=self.p_char_name).value, self.p_char_value)
        self.assertEqual(
            copied_instance.property(name=self.p_multi_name).value, self.p_multi_value
        )
        self.assertEqual(copied_instance.property(name=self.p_int_name).value, self.p_int_value)
        self.assertEqual(
            copied_instance.property(name=self.p_float_name).value, self.p_float_value
        )
        self.assertEqual(copied_instance.property(name=self.p_bool_name).value, self.p_bool_value)
        self.assertEqual(copied_instance.property(name=self.p_date_name).value, self.p_date_value)
        self.assertIn(
            self.p_datetime_value, copied_instance.property(name=self.p_datetime_name).value
        )
        self.assertIn('requirements.txt',
                      copied_instance.property(name=self.p_attach_name).filename)
        self.assertIn('requirements.txt', self.p_attach_value)
        self.assertEqual(copied_instance.property(name=self.p_link_name).value, self.p_link_value)
        self.assertEqual(
            copied_instance.property(name=self.p_single_select_name).value,
            self.p_single_select_value,
        )
        self.assertEqual(
            copied_instance.property(name=self.p_multi_select_name).value,
            self.p_multi_select_value,
        )
        list_of_parts_ids = [
            part.id
            for part in copied_instance.property(name=self.p_part_reference_name_cross_scope).value
        ]
        list_of_user_ids = [
            user.id for user in copied_instance.property(name=self.p_user_reference_name).value
        ]
        self.assertIn(self.front_wheel.id, list_of_parts_ids)
        self.assertIn(self.rear_wheel.id, list_of_parts_ids)
        self.assertIn(
            self.specify_wheel_diameter.id,
            [
                act.id
                for act in copied_instance.property(name=self.p_activity_reference_name).value
            ],
        )
        self.assertIn(
            self.project.id,
            [
                scope.id
                for scope in copied_instance.property(name=self.p_project_reference_name).value
            ],
        )
        self.assertIn(self.test_manager.id, list_of_user_ids)
        self.assertIn(self.test_supervisor.id, list_of_user_ids)

        self.assertEqual(len(copied_instance._cached_children), 2)

    def test_move_part_instance(self):
        # setUp
        multiplicity_model = self.model_to_be_copied.add_model(
            name="__multiplicity part", multiplicity=Multiplicity.ZERO_MANY
        )
        multiplicity_part1 = self.instance_to_be_copied.add(
            model=multiplicity_model,
            name="__multiplicity part instance 1",
        )
        multiplicity_part2 = self.instance_to_be_copied.add(
            model=multiplicity_model,
            name="__multiplicity part instance 2",
        )

        clone_of_original_instance = multiplicity_part2.clone()

        moved_instance = clone_of_original_instance.move(
            target_parent=self.project.part("Bike"),
            name="__Moved clone instance",
            include_children=False,
        )

        moved_instance.populate_descendants()
        self.dump_part = moved_instance.model()

        # testing
        with self.assertRaises(NotFoundError):
            self.project.model(name=clone_of_original_instance.name)

        self.assertTrue(moved_instance)
        self.assertEqual(len(moved_instance.properties), 0)

    def test_copy_different_categories(self):
        target_instance = self.project.part(name="Bike")

        with self.assertRaisesRegex(IllegalArgumentError, "must have the same category"):
            self.model_to_be_copied.copy(target_parent=target_instance)

    def test_move_different_categories(self):
        target_instance = self.project.part(name="Bike")

        with self.assertRaisesRegex(IllegalArgumentError, "must have the same category"):
            self.model_to_be_copied.move(target_parent=target_instance)

    def test_copy_target_parent_inside_tree(self):
        with self.assertRaises(IllegalArgumentError):
            self.model_to_be_copied.copy(
                target_parent=self.sub_part1,
            )

    def test_copy_missing_target_parent_instance(self):
        target_parent = self.project.product_root_model.add_model(
            name="__ZERO+ MODEL",
            multiplicity=Multiplicity.ZERO_MANY,
        )
        self.dump_part = target_parent
        with self.assertRaises(IllegalArgumentError):
            self.model_to_be_copied.copy(
                target_parent=target_parent,
                include_instances=True,
            )

    def test_copy_too_many_target_parent_instances(self):
        target_parent = self.project.product_root_model.add_model(
            name="__ONE+ MODEL",
            multiplicity=Multiplicity.ONE_MANY,
        )
        self.project.product_root_instance.add(model=target_parent)
        self.dump_part = target_parent
        with self.assertRaises(IllegalArgumentError):
            self.model_to_be_copied.copy(
                target_parent=target_parent,
                include_instances=True,
            )

    def test_copy_attachments(self):
        names = [
            "__Property attachment_1",
            "__Property attachment_2",
        ]

        for name in names:
            self.model_to_be_copied.add_property(
                name=name,
                property_type=PropertyType.ATTACHMENT_VALUE,
            )

        self.instance_to_be_copied.refresh()

        for name in names:
            p_attachment = self.instance_to_be_copied.property(name)
            file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "requirements.txt")
            p_attachment.upload(file)

        self.dump_part = self.model_to_be_copied.copy(
            target_parent=self.model_target_parent,
        )

        copied_instance = self.dump_part.instance()

        for name in names:
            copied_prop = copied_instance.property(name)
            self.assertTrue(copied_prop.has_value())

    def test_cross_scope_copy(self):
        name_of_part = "__Copied model under Bike"
        self.dump_part = self.model_to_be_copied.copy(
            target_parent=self.cross_scope_bike,
            name=name_of_part,
            include_children=True,
            include_instances=True,
        )

        self.dump_part.refresh()
        copied_options = self.dump_part.property(self.p_part_reference_name_cross_scope)._options
        self.assertTrue(self.model_to_be_copied.scope_id == copied_options.get("scope_id"))

        copied_sub_part2_int_prop = self.dump_part(self.sub_part2.name).property(self.p_int_name)
        copied_sub_part2_bool_prop = self.dump_part(self.sub_part2.name).property(self.p_bool_name)

        copied_part_ref_options = self.dump_part.property(self.p_part_reference_name)._options
        copied_scope_ref_options = self.dump_part.property(self.p_project_reference_name)._options

        self.assertTrue(self.dump_part.scope_id == copied_part_ref_options.get("scope_id"))
        self.assertTrue(
            copied_sub_part2_bool_prop.id in copied_part_ref_options.get("propmodels_excl"))
        self.assertTrue(
            copied_sub_part2_int_prop.id in copied_part_ref_options["prefilters"]["property_value"]
        )
        self.assertEqual(ScopeStatus.ACTIVE, copied_scope_ref_options["prefilters"]["status__in"])
        self.assertEqual("bike", copied_scope_ref_options["prefilters"]["tags__contains"])
