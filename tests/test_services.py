import time

import os
import pytest

from pykechain.enums import ServiceExecutionStatus, ServiceType
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from tests.classes import TestBetamax
# new in 1.13
from pykechain.utils import temp_chdir


class TestServiceSetup(TestBetamax):
    """Only for test setup, will create a service with a debug script

    :ivar service: service with a debug.py script
    """
    def _create_service(self, name=None):
        """Creates a service with name, and adds a test_upload_script.py (debugging)"""
        # setUp
        new_service = self.project.create_service(
            name=name or 'Test upload script to service',
            description="Only used for testing - you can safely remove this"
        )
        upload_path = os.path.join(self.test_assets_dir, 'tests', 'files', 'uploaded', 'test_upload_script.py')

        # testing
        new_service.upload(pkg_path=upload_path)
        self.assertEqual(new_service._json_data['script_file_name'], 'test_upload_script.py')
        return new_service

    def setUp(self):
        super(TestServiceSetup, self).setUp()
        self.test_assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))
        self.service = self._create_service()

    def tearDown(self):
        self.service.delete()
        super(TestServiceSetup, self).tearDown()

class TestServices(TestBetamax):
    def _create_service(self, name=None):
        """Creates a service with name, and adds a test_upload_script.py (debugging)"""
        # setUp
        new_service = self.project.create_service(
            name=name or 'Test upload script to service',
            description="Only used for testing - you can safely remove this"
        )
        upload_path = os.path.join(self.test_assets_dir, 'tests', 'files', 'uploaded', 'test_upload_script.py')

        # testing
        new_service.upload(pkg_path=upload_path)
        new_service.refresh()
        self.assertEqual(new_service._json_data['script_file_name'], 'test_upload_script.py')
        return new_service

    def setUp(self):
        super(TestServices, self).setUp()
        self.test_assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))

    def test_retrieve_services(self):
        self.assertTrue(self.project.services())

    def test_retrieve_services_with_kwargs(self):
        # setUp
        retrieved_services_with_kwargs = self.project.services(env_version="3.5")

        # testing
        self.assertTrue(retrieved_services_with_kwargs)
        for service in retrieved_services_with_kwargs:
            self.assertEqual(service._json_data['env_version'], '3.5')

    def test_retrieve_service_but_found_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.service(script_type=ServiceType.PYTHON_SCRIPT)

    def test_retrieve_single_service(self):
        services = self.project.services()
        self.assertTrue(services)
        service_1 = services[0]

        self.assertEqual(self.project.service(pk=service_1.id), service_1)

    def test_retrieve_service_by_name(self):
        service_name = 'Service Gears - Successful'
        service = self.project.service(name=service_name)
        self.assertTrue(service)
        self.assertEqual(service.name, service_name)

    @pytest.mark.skipif("os.getenv('TRAVIS', False)",
                        reason="Skipping tests when using Travis, as Service Execution cannot be provided")
    def test_debug_service_execute(self):
        service_name = 'Service Gears - Successful'
        service = self.project.service(name=service_name)

        service_execution = service.execute()
        self.assertTrue(service_execution.status in ServiceExecutionStatus.values())
        if service_execution.status in (ServiceExecutionStatus.LOADING, ServiceExecutionStatus.RUNNING):
            # sleep 2000 ms
            time.sleep(2)
            service_execution.refresh()
            self.assertTrue(service_execution.status in ServiceExecutionStatus.values())
        self.assertEqual(ServiceExecutionStatus.FAILED, service_execution.status,
                         "The service execution is status 'FAILED', please upload working debugging scripts before "
                         "running the tests")

    def test_update_service(self):
        # setUp
        service_name = 'Service Gears - Successful'
        service = self.project.service(name=service_name)
        version_before = str(service.version)
        name_before = service_name
        name_after = 'Pykechain needs no debugging'
        description_before = str(service._json_data['description'])
        description_after = 'Pykechain is way too good for that'
        version_after = '-latest'

        # testing
        service.edit(name=name_after, description=description_after, version=version_after)
        service.refresh()
        self.assertEqual(service.name, name_after)
        self.assertEqual(service._json_data['description'], description_after)
        self.assertEqual(service.version, version_after)

        # tearDown
        service.edit(name=name_before, description=description_before, version=version_before)


class TestServicesWithCustomUploadedService(TestServiceSetup):



    def test_update_service_incorrect_name(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(name=1234)

    def test_update_service_incorrect_description(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(description=True)

    def test_update_service_incorrect_version(self):
        with self.assertRaises(IllegalArgumentError):
            self.service.edit(version=['2.0'])

    def test_service_refresh_from_kechain(self):
        version_after = '-latest'
        self.service.edit(version=version_after)
        self.service.refresh()
        self.assertEqual(self.service.version, version_after)


    def test_get_executions_of_service(self):
        self.assertTrue(len(self.service.get_executions()) >= 0)

    def test_create_and_delete_service(self):
        service_name = 'Test service creation'
        new_service = self.project.create_service(service_name)

        self.assertTrue(new_service.name, service_name)
        self.assertTrue(new_service)

        # tearDown
        new_service.delete()
        with self.assertRaisesRegex(NotFoundError, 'No service fits criteria'):
            self.project.service(pk=new_service.id)

    def test_create_service_with_wrong_service_type(self):
        with self.assertRaisesRegex(IllegalArgumentError, 'The type should be of one of'):
            self.project.create_service(name='This service type does not exist', service_type='RUBY_SCRIPT')

    def test_create_service_with_wrong_environment_version(self):
        with self.assertRaisesRegex(IllegalArgumentError, 'The environment version should be of one of'):
            self.project.create_service(name='This env version does not exist', environment_version='0.0')

    def test_save_service_script(self):
        # setUp
        with temp_chdir() as target_dir:
            self.service.save_as(target_dir=target_dir)
            self.assertEqual(len(os.listdir(target_dir)), 1)

    def test_upload_script_to_service(self):
        # setUp
        upload_path = os.path.join(self.test_assets_dir, 'tests', 'files', 'uploaded', 'test_upload_script.py')

        # testing
        self.service.upload(pkg_path=upload_path)
        # second upload modified filename
        self.assertRegex(self.service._json_data['script_file_name'], 'test_upload_\w+.py')

    def test_upload_script_to_service_with_wrong_path(self):
        # setUp
        upload_path = os.path.join(self.test_assets_dir, 'tests', 'files', 'uploaded', 'this_file_does_exists.not')

        # testing
        with self.assertRaisesRegex(OSError, 'Could not locate python package to upload in'):
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

        self.assertEqual(self.project.service_execution(pk=service_execution_1.id), service_execution_1)

    def test_retrieve_single_service_execution_but_found_none(self):
        with self.assertRaises(NotFoundError):
            self.project.service_execution(username='No service execution as this user does not exist')

    def test_retrieve_single_service_execution_but_found_multiple(self):
        # setUp
        self.service.execute()
        self.service.execute()

        # testing
        with self.assertRaises(MultipleFoundError):
            self.project.service_execution(service=self.service.id)

    @pytest.mark.skipif("os.getenv('TRAVIS', False)",
                        reason="Skipping tests when using Travis, as Service Execution cannot be provided")
    def test_debug_service_execution_terminate(self):
        service_execution = self.service.execute()
        service_execution.refresh()
        self.assertEqual(service_execution.status, ServiceExecutionStatus.LOADING)
        time.sleep(2)
        service_execution.refresh()
        self.assertEqual(service_execution.status, ServiceExecutionStatus.RUNNING)
        service_execution.terminate()

        self.assertFalse(service_execution.status == ServiceExecutionStatus.FAILED,
                         "The service execution is status 'FAILED', please upload working debugging scripts before "
                         "running the tests")

    def test_log_of_service_execution(self):
        # setUp
        service_execution = self.service.execute()

        with temp_chdir() as target_dir:
            service_execution.get_log(target_dir=target_dir)
            log_file = os.path.join(target_dir, 'log.txt')
            self.assertTrue(log_file)
