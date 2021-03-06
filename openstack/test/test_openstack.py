# (C) Datadog, Inc. 2010-2017
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

# stdlib
from nose.plugins.attrib import attr
from time import sleep
from unittest import TestCase
from mock import patch
import re

# 3p

# project
from tests.checks.common import AgentCheckTest, load_class
from checks import AgentCheck


OS_CHECK_NAME = 'openstack'
OS_CHECK_MODULE = 'openstack.openstack'

OpenStackProjectScope = load_class(OS_CHECK_MODULE, "OpenStackProjectScope")
KeystoneCatalog = load_class(OS_CHECK_MODULE, "KeystoneCatalog")
IncompleteConfig = load_class(OS_CHECK_MODULE, "IncompleteConfig")
IncompleteAuthScope = load_class(OS_CHECK_MODULE, "IncompleteAuthScope")
IncompleteIdentity = load_class(OS_CHECK_MODULE, "IncompleteIdentity")


class MockHTTPResponse(object):
    def __init__(self, response_dict, headers):
        self.response_dict = response_dict
        self.headers = headers

    def json(self):
        return self.response_dict


EXAMPLE_AUTH_RESPONSE = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'roles': [
            {
                u'id': u'f20c215f5a4d47b7a6e510bc65485ced',
                u'name': u'datadog_monitoring'
            },
            {
                u'id': u'9fe2ff9ee4384b1894a90878d3e92bab',
                u'name': u'_member_'
            }
        ],
        u'expires_at': u'2015-11-02T15: 57: 43.911674Z',
        u'project': {
            u'domain': {
                u'id': u'default',
                u'name': u'Default'
            },
            u'id': u'0850707581fe4d738221a72db0182876',
            u'name': u'admin'
        },
        u'catalog': [
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:8773/',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'541baeb9ab7542609d7ae307a7a9d5f0'
                    },
                    {
                        u'url': u'http: //10.0.2.15:8773/',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'5c648acaea9941659a5dc04fb3b18e49'
                    },
                    {
                        u'url': u'http: //10.0.2.15:8773/',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'cb70e610620542a1804522d365226981'
                    }
                ],
                u'type': u'compute',
                u'id': u'1398dc02f9b7474eb165106485033b48',
                u'name': u'nova'
            },
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'354e35ed19774e398f80dc2a90d07f4b'
                    },
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'36e8e2bf24384105b9d56a65b0900172'
                    },
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'de93edcbf7f9446286687ec68423c36f'
                    }
                ],
                u'type': u'computev21',
                u'id': u'2023bd4f451849ba8abeaaf283cdde4f',
                u'name': u'novav21'
            },
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'7c1e318d8f7f42029fcb591598df2ef5'
                    },
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'afcc88b1572f48a38bb393305dc2b584'
                    },
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'd9730dbdc07844d785913219da64a197'
                    }
                ],
                u'type': u'network',
                u'id': u'21ad241f26194bccb7d2e49ee033d5a2',
                u'name': u'neutron'
            },

        ],
        u'extras': {

        },
        u'user': {
            u'domain': {
                u'id': u'default',
                u'name': u'Default'
            },
            u'id': u'5f10e63fbd6b411186e561dc62a9a675',
            u'name': u'datadog'
        },
        u'audit_ids': [
            u'OMQQg9g3QmmxRHwKrfWxyQ'
        ],
        u'issued_at': u'2015-11-02T14: 57: 43.911697Z'
    }
}
MOCK_HTTP_RESPONSE = MockHTTPResponse(response_dict=EXAMPLE_AUTH_RESPONSE, headers={"X-Subject-Token": "fake_token"})

@attr(requires='openstack')
class OSProjectScopeTest(TestCase):
    BAD_AUTH_SCOPES = [
        {"auth_scope": {}},
        {"auth_scope": {"project": {}}},
        {"auth_scope": {"project": {"id": ""}}},
        {"auth_scope": {"project": {"name": "test"}}},
        {"auth_scope": {"project": {"name": "test", "domain": {}}}},
        {"auth_scope": {"project": {"name": "test", "domain": {"id": ""}}}},
    ]

    GOOD_AUTH_SCOPES = [
        {"auth_scope": {"project": {"id": "test_project_id"}}},
        {"auth_scope": {"project": {"name": "test", "domain": {"id": "test_id"}}}},
    ]

    BAD_USERS = [
        {"user": {}},
        {"user": {"name": ""}},
        {"user": {"name": "test_name", "password": ""}},
        {"user": {"name": "test_name", "password": "test_pass", "domain": {}}},
        {"user": {"name": "test_name", "password": "test_pass", "domain": {"id": ""}}},
    ]

    GOOD_USERS = [
        {"user": {"name": "test_name", "password": "test_pass", "domain": {"id": "test_id"}}},
    ]

    def _test_bad_auth_scope(self, scope):
        self.assertRaises(IncompleteAuthScope, OpenStackProjectScope.get_auth_scope, scope)

    def test_get_auth_scope(self):
        for scope in self.BAD_AUTH_SCOPES:
            self._test_bad_auth_scope(scope)

        for scope in self.GOOD_AUTH_SCOPES:
            auth_scope = OpenStackProjectScope.get_auth_scope(scope)

            # Should pass through unchanged
            self.assertEqual(auth_scope, scope.get("auth_scope"))

    def _test_bad_user(self, user):
        self.assertRaises(IncompleteIdentity, OpenStackProjectScope.get_user_identity, user)


    def test_get_user_identity(self):
        for user in self.BAD_USERS:
            self._test_bad_user(user)

        for user in self.GOOD_USERS:
            parsed_user = OpenStackProjectScope.get_user_identity(user)
            self.assertEqual(parsed_user, {"methods": ["password"], "password": user})

    def test_from_config(self):
        init_config = {"keystone_server_url": "http://10.0.2.15:5000", "nova_api_version": "v2"}
        bad_instance_config = {}

        good_instance_config = {"user": self.GOOD_USERS[0]["user"], "auth_scope": self.GOOD_AUTH_SCOPES[0]["auth_scope"]}

        self.assertRaises(IncompleteConfig, OpenStackProjectScope.from_config, init_config, bad_instance_config)

        with patch("datadog_checks.openstack.openstack.OpenStackProjectScope.request_auth_token", return_value=MOCK_HTTP_RESPONSE):
            append_config = good_instance_config.copy()
            append_config["append_tenant_id"] = True
            scope = OpenStackProjectScope.from_config(init_config, append_config)
            self.assertTrue(isinstance(scope, OpenStackProjectScope))

            self.assertEqual(scope.auth_token, "fake_token")
            self.assertEqual(scope.tenant_id, "test_project_id")

            # Test that append flag worked
            self.assertEqual(scope.service_catalog.nova_endpoint, "http://10.0.2.15:8773/test_project_id")


@attr(requires='openstack')
class KeyStoneCatalogTest(TestCase):

    def test_get_nova_endpoint(self):
        self.assertEqual(KeystoneCatalog.get_nova_endpoint(EXAMPLE_AUTH_RESPONSE), u"http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876")
        self.assertEqual(KeystoneCatalog.get_nova_endpoint(EXAMPLE_AUTH_RESPONSE, nova_api_version="v2"), u"http://10.0.2.15:8773/")

    def test_get_neutron_endpoint(self):
        self.assertEqual(KeystoneCatalog.get_neutron_endpoint(EXAMPLE_AUTH_RESPONSE), u"http://10.0.2.15:9292")

    def test_from_auth_response(self):
        catalog = KeystoneCatalog.from_auth_response(EXAMPLE_AUTH_RESPONSE, "v2.1")
        self.assertTrue(isinstance(catalog, KeystoneCatalog))
        self.assertEqual(catalog.neutron_endpoint, u"http://10.0.2.15:9292")
        self.assertEqual(catalog.nova_endpoint, u"http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876")


@attr(requires='openstack')
class TestOpenstack(AgentCheckTest):
    """Test for openstack integration."""
    CHECK_NAME = OS_CHECK_NAME

    # Samples
    # .. server/network
    ALL_IDS = ["server-1", "server-2", "other-1", "other-2"]
    EXCLUDED_NETWORK_IDS = ["server-1", "other-.*"]
    EXCLUDED_SERVER_IDS = ["server-2", "other-.*"]
    FILTERED_NETWORK_ID = "server-2"
    FILTERED_SERVER_ID = "server-1"

    # .. config
    MOCK_CONFIG = {
        "init_config": {
            "keystone_server_url": "http://10.0.2.15:5000",
            "ssl_verify": False,
            "exclude_network_ids": EXCLUDED_NETWORK_IDS,
        },
        "instances": [
            {
                "name": "test_name", "user": {"name": "test_name", "password": "test_pass", "domain": {"id": "test_id"}},
                "auth_scope": {"project": {"id": "test_project_id"}},
            }
        ]
    }

    def setUp(self):
        self.load_check(self.MOCK_CONFIG, self.DEFAULT_AGENT_CONFIG)

    def test_ensure_auth_scope(self):
        instance = self.MOCK_CONFIG["instances"][0]
        instance['tags'] = ['optional:tag1']

        self.assertRaises(KeyError, self.check.get_scope_for_instance, instance)

        with patch("datadog_checks.openstack.openstack.OpenStackProjectScope.request_auth_token", return_value=MOCK_HTTP_RESPONSE):
            scope = self.check.ensure_auth_scope(instance)

            self.assertEqual(self.check.get_scope_for_instance(instance), scope)
            self.check._send_api_service_checks(scope, ['optional:tag1'])

            self.service_checks = self.check.get_service_checks()
            # Sort the tags list
            for sc in self.service_checks:
                sc["tags"].sort()
            tags = ['keystone_server:http://10.0.2.15:5000', 'optional:tag1']
            tags.sort()

            # Expect OK, since we've mocked an API response
            self.assertServiceCheck(self.check.IDENTITY_API_SC, status=AgentCheck.OK, count=1, tags=tags)

            # Expect CRITICAL since URLs are non-existent
            self.assertServiceCheck(self.check.COMPUTE_API_SC, status=AgentCheck.CRITICAL, count=1, tags=tags)
            self.assertServiceCheck(self.check.NETWORK_API_SC, status=AgentCheck.CRITICAL, count=1, tags=tags)

            self.check._current_scope = scope

        self.check.delete_current_scope()
        self.assertRaises(KeyError, self.check.get_scope_for_instance, instance)

    def test_parse_uptime_string(self):
        uptime_parsed = self.check._parse_uptime_string(u' 16:53:48 up 1 day, 21:34,  3 users,  load average: 0.04, 0.14, 0.19\n')
        self.assertEqual(uptime_parsed.get('loads'), [0.04, 0.14, 0.19])

    def test_cache_utils(self):
        self.check.CACHE_TTL["aggregates"] = 1
        expected_aggregates = {"hyp_1": ["aggregate:staging", "availability_zone:test"]}

        with patch("datadog_checks.openstack.OpenStackCheck.get_all_aggregate_hypervisors", return_value=expected_aggregates):
            self.assertEqual(self.check._get_and_set_aggregate_list(), expected_aggregates)
            sleep(1.5)
            self.assertTrue(self.check._is_expired("aggregates"))

    @patch("datadog_checks.openstack.OpenStackCheck.get_all_server_ids", return_value=ALL_IDS)
    def test_server_exclusion(self, *args):
        """
        Exclude networks using regular expressions.
        """

        self.check.exclude_server_id_rules = set([re.compile(rule) for rule in self.EXCLUDED_SERVER_IDS])

        # Retrieve servers
        server_ids = self.check.get_servers_managed_by_hypervisor()

        # Assert
        # .. 1 out of 4 server ids filtered
        self.assertEqual(len(server_ids), 1)
        self.assertEqual(server_ids[0], self.FILTERED_SERVER_ID)

        # cleanup
        self.check.exclude_server_id_rules = set([])

    @patch("datadog_checks.openstack.OpenStackCheck.get_all_network_ids", return_value=ALL_IDS)
    def test_network_exclusion(self, *args):
        """
        Exclude networks using regular expressions.
        """
        with patch("datadog_checks.openstack.OpenStackCheck.get_stats_for_single_network") \
                as mock_get_stats_single_network:

            self.check.exclude_network_id_rules = set([re.compile(rule) for rule in self.EXCLUDED_NETWORK_IDS])

            # Retrieve network stats
            self.check.get_network_stats([])

            # Assert
            # .. 1 out of 4 network filtered in
            self.assertEqual(mock_get_stats_single_network.call_count, 1)
            self.assertEqual(
                mock_get_stats_single_network.call_args[0][0], self.FILTERED_NETWORK_ID
            )

            # cleanup
            self.check.exclude_network_id_rules = set([])
