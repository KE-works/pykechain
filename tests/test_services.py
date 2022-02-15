import os
import time
from datetime import datetime

import pytest

from pykechain.enums import ServiceEnvironmentVersion, ServiceExecutionStatus, ServiceType
from pykechain.exceptions import APIError, IllegalArgumentError, MultipleFoundError, NotFoundError

# new in 1.13
from pykechain.models import Service
from pykechain.utils import temp_chdir
from tests.classes import TestBetamax


class TestServiceSetup(TestBetamax):
    """Only for test setup, will create a service with a debug script

    :ivar service: service with a debug.py script
    """

    def _create_service(self, name=None):
        """Creates a service with name, and adds a test_upload_script.py (debugging)"""
        # setUp
        new_service = self.project.create_service(
            name=name or "Test upload script to service",
            description="Only used for testing - you can safely remove this",
            environment_version=ServiceEnvironmentVersion.PYTHON_3_8,
        )
        upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_script_to_service",
            "test_upload_script.py",
        )

        # testing
        new_service.upload(pkg_path=upload_path)
        self.assertEqual(new_service._json_data["script_file_name"], "test_upload_script.py")
        return new_service

    def setUp(self):
        super().setUp()
        self.test_assets_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.service = self._create_service()

    def tearDown(self):
        self.service.delete()
        super().tearDown()


class TestServices(TestBetamax):
    def _create_service(self, name=None):
        """Creates a service with name, and adds a test_upload_script.py (debugging)"""
        # setUp
        new_service = self.project.create_service(
            name=name or "Test upload script to service",
            description="Only used for testing - you can safely remove this",
        )
        upload_path = os.path.join(
            self.test_assets_dir, "tests", "files", "uploaded", "test_upload_script.py"
        )

        # testing
        new_service.upload(pkg_path=upload_path)
        new_service.refresh()
        self.assertEqual(new_service._json_data["script_file_name"], "test_upload_script.py")
        return new_service

    def setUp(self):
        super().setUp()
        self.test_assets_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )

    def test_retrieve_services(self):
        self.assertTrue(self.project.services())

    def test_retrieve_services_with_kwargs(self):
        # setUp
        retrieved_services_with_kwargs = self.project.services(
            script_type=ServiceType.PYTHON_SCRIPT
        )

        # testing
        self.assertTrue(retrieved_services_with_kwargs)
        for service in retrieved_services_with_kwargs:
            self.assertEqual(ServiceType.PYTHON_SCRIPT, service._json_data["script_type"])

    def test_retrieve_service_but_found_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.service(script_type=ServiceType.PYTHON_SCRIPT)

    def test_retrieve_single_service(self):
        services = self.project.services()
        self.assertTrue(services)
        service_1 = services[0]

        self.assertEqual(self.project.service(pk=service_1.id), service_1)

    def test_retrieve_service_by_name(self):
        service_name = "Service Gears - Successful"
        service = self.project.service(name=service_name)
        self.assertTrue(service)
        self.assertEqual(service.name, service_name)

    def test_properties_of_service(self):
        service_name = "Service Gears - Successful with Package"
        service = self.project.service(name=service_name)

        for key, value in service.__dict__.items():
            if str(key).startswith("_"):
                continue

            # Verified on is an optional variable
            if key == "verified_on":
                continue

            with self.subTest(msg=f"{key}: {value}"):
                self.assertIsNotNone(value)

    @pytest.mark.skipif(
        "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
        reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
    )
    def test_debug_service_execute(self):
        service_name = "Service Gears - Successful"
        service = self.project.service(name=service_name)

        service_execution = service.execute()
        self.assertTrue(service_execution.status in ServiceExecutionStatus.values())
        if service_execution.status in (
            ServiceExecutionStatus.LOADING,
            ServiceExecutionStatus.RUNNING,
        ):
            # sleep 2000 ms
            time.sleep(2)
            service_execution.refresh()
            self.assertTrue(service_execution.status in ServiceExecutionStatus.values())

    @pytest.mark.skipif(
        "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
        reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
    )
    def test_service_context(self):
        some_activity = self.project.activities()[0]
        service = self.project.service(name="Service Gears - Successful")

        service_execution = service.execute(activity_id=some_activity.id)
        self.assertEqual(some_activity.id, service_execution.activity_id)

    def test_update_service(self):
        # setUp
        service_name = "Service Gears - Successful"
        service = self.project.service(name=service_name)
        version_before = str(service.version)
        name_before = service_name
        name_after = "Pykechain needs no debugging"
        description_before = str(service._json_data["description"])
        description_after = "Pykechain is way too good for that"
        version_after = "-latest"

        # testing
        service.edit(name=name_after, description=description_after, version=version_after)
        service.refresh()
        self.assertEqual(service.name, name_after)
        self.assertEqual(service._json_data["description"], description_after)
        self.assertEqual(service.version, version_after)

        # tearDown
        service.edit(name=name_before, description=description_before, version=version_before)

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_service_clear_values(self):
        # setup
        initial_name = "Service testing editing"
        initial_description = "Description test"
        initial_version = "1.0"
        initial_run_as = "kenode"
        initial_trusted = False
        initial_type = ServiceType.NOTEBOOK
        initial_env = ServiceEnvironmentVersion.PYTHON_3_8_NOTEBOOKS
        # TODO: to be removed in later versions of pykechain, only for temporal compatibility
        compatibility_env = "3.7_notebook"

        self.service = self.project.create_service(name=initial_name)

        self.service.edit(
            name=initial_name,
            description=initial_description,
            version=initial_version,
            type=initial_type,
            environment_version=initial_env,
            run_as=initial_run_as,
            trusted=initial_trusted,
        )

        # Edit without mentioning values, everything should stay the same
        new_name = "Changed service name"

        self.service.edit(name=new_name)

        # testing
        self.assertEqual(self.service.name, new_name)
        self.assertEqual(self.service.description, initial_description)
        self.assertEqual(self.service.version, initial_version)
        self.assertEqual(self.service.run_as, initial_run_as)
        self.assertEqual(self.service.type, initial_type)
        self.assertIn(self.service.environment, (initial_env, compatibility_env))
        self.assertEqual(self.service.trusted, initial_trusted)

        # Edit with clearing the values, name and status cannot be cleared
        self.service.edit(
            name=None,
            description=None,
            version=None,
            type=None,
            environment_version=None,
            run_as=None,
            trusted=None,
        )

        self.assertEqual(self.service.name, new_name)
        self.assertEqual(self.service.description, "")
        self.assertEqual(self.service.version, "")
        self.assertEqual(self.service.type, initial_type)
        self.assertIn(self.service.environment, (initial_env, compatibility_env))
        self.assertEqual(self.service.run_as, initial_run_as)
        self.assertEqual(self.service.trusted, initial_trusted)

        # teardown
        self.service.delete()

    # test added in 3.1
    def test_retrieve_services_with_refs(self):
        # setup
        service_ref = "service-gears-successful"
        service_name = "Service Gears - Successful"
        service = self.project.service(ref=service_ref)

        # testing
        self.assertIsInstance(service, Service)
        self.assertTrue(service.name, service_name)


class TestServicesWithCustomUploadedService(TestServiceSetup):
    def test_update_service_incorrect_name(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(name=1234)

    def test_update_service_incorrect_description(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(description=True)

    def test_update_service_incorrect_version(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(version=["2.0"])

    def test_service_refresh_from_kechain(self):
        version_after = "-latest"
        self.service.edit(version=version_after)
        self.service.refresh()
        self.assertEqual(self.service.version, version_after)

    def test_get_executions_of_service(self):
        self.assertTrue(len(self.service.get_executions()) >= 0)

    def test_create_and_delete_service(self):
        service_name = "Test service creation"
        new_service = self.project.create_service(service_name)

        self.assertTrue(new_service.name, service_name)
        self.assertTrue(new_service)

        # tearDown
        new_service.delete()
        with self.assertRaisesRegex(NotFoundError, "fit criteria"):
            self.project.service(pk=new_service.id)

    def test_create_service_with_wrong_service_type(self):
        with self.assertRaisesRegex(IllegalArgumentError, "must be an option from enum"):
            self.project.create_service(
                name="This service type does not exist", service_type="RUBY_SCRIPT"
            )

    def test_create_service_with_wrong_environment_version(self):
        with self.assertRaisesRegex(IllegalArgumentError, "must be an option from enum"):
            self.project.create_service(
                name="This env version does not exist", environment_version="0.0"
            )

    def test_save_service_script(self):
        # setUp
        with temp_chdir() as target_dir:
            self.service.save_as(target_dir=target_dir)
            self.assertEqual(len(os.listdir(target_dir)), 1)

    def test_upload_script_to_service(self):
        # setUp
        upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_script_to_service",
            "test_upload_script.py",
        )

        # testing
        self.service.upload(pkg_path=upload_path)
        # second upload modified filename
        self.assertRegex(self.service._json_data["script_file_name"], r"test_upload_\w+.py")

    def test_upload_script_to_service_with_wrong_path(self):
        # setUp
        upload_path = os.path.join(
            self.test_assets_dir, "tests", "files", "uploaded", "this_file_does_exists.not"
        )

        # testing
        with self.assertRaisesRegex(OSError, "Could not locate python package to upload in"):
            self.service.upload(pkg_path=upload_path)


# new in 1.13
class TestServiceExecutions(TestServiceSetup):
    def test_retrieve_service_executions(self):
        self.assertTrue(self.project.service_executions())

    def test_retrieve_service_executions_with_kwargs(self):
        # setUp
        limit = 15
        retrieved_executions_with_kwargs = self.project.service_executions(limit=limit)

        # testing
        self.assertTrue(len(retrieved_executions_with_kwargs) <= limit)

    def test_retrieve_single_service_execution(self):
        service_executions = self.project.service_executions()
        self.assertTrue(service_executions)
        service_execution_1 = service_executions[0]

        self.assertEqual(
            self.project.service_execution(pk=service_execution_1.id), service_execution_1
        )

    def test_retrieve_single_service_execution_but_found_none(self):
        with self.assertRaises(NotFoundError):
            self.project.service_execution(
                username="No service execution as this user does not exist"
            )

    def test_retrieve_single_service_execution_but_found_multiple(self):
        # setUp
        service_execution = self.service.execute()
        while service_execution.status in [
            ServiceExecutionStatus.LOADING,
            ServiceExecutionStatus.RUNNING,
        ]:
            time.sleep(0.500)  # 200ms
            service_execution.refresh()

        self.service.execute()

        # testing
        with self.assertRaises(MultipleFoundError):
            self.project.service_execution(service=self.service.id)

    def test_service_execution_conflict(self):
        # setUp
        self.service.execute()

        # testing
        with self.assertRaisesRegex(APIError, "Conflict: Could not execute"):
            self.service.execute()

    def test_properties_of_service_execution(self):
        service_name = "Service Gears - Successful"
        service = self.project.service(name=service_name)

        service_executions = self.project.service_executions(service=service.id, limit=1)
        self.assertTrue(service_executions)

        service_execution = service_executions[0]

        self.assertIsInstance(service_execution.service, Service)
        self.assertIsInstance(service_execution.started_at, datetime)
        self.assertIsInstance(service_execution.finished_at, datetime)

        for key, value in service_execution.__dict__.items():
            if str(key).startswith("_"):
                continue

            # Originating activity is an optional variable
            if key == "activity_id" or key == "ref":
                continue

            with self.subTest(msg=f"{key}: {value}"):
                self.assertIsNotNone(value)

    @pytest.mark.skipif(
        "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
        reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
    )
    def test_debug_service_execution_terminate(self):
        service_execution = self.service.execute()
        self.assertEqual(service_execution.status, ServiceExecutionStatus.LOADING)
        time.sleep(2)
        service_execution.refresh()
        self.assertEqual(service_execution.status, ServiceExecutionStatus.RUNNING)
        service_execution.terminate()

        self.assertNotEqual(
            service_execution.status,
            ServiceExecutionStatus.FAILED,
            "The service execution is status 'FAILED', please upload working debugging scripts"
            " before running the tests",
        )

    def test_log_of_service_execution(self):
        # setUp
        service_execution = self.service.execute()
        time.sleep(5)

        with temp_chdir() as target_dir:
            service_execution.get_log(target_dir=target_dir)
            log_file = os.path.join(target_dir, "log.txt")
            self.assertTrue(log_file)
