"""
    Aries Cloud Agent + didcomm_resolver Plugin

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: v0.6.0
    Generated by: https://openapi-generator.tech
"""


import unittest

import acapy_client
from acapy_client.api.schema_api import SchemaApi  # noqa: E501


class TestSchemaApi(unittest.TestCase):
    """SchemaApi unit test stubs"""

    def setUp(self):
        self.api = SchemaApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_schemas_created_get(self):
        """Test case for schemas_created_get

        Search for matching schema that agent originated  # noqa: E501
        """
        pass

    def test_schemas_post(self):
        """Test case for schemas_post

        Sends a schema to the ledger  # noqa: E501
        """
        pass

    def test_schemas_schema_id_get(self):
        """Test case for schemas_schema_id_get

        Gets a schema from the ledger  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()