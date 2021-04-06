"""Didcommm Universal DID Resolver."""

import json
import os
from pathlib import Path
from typing import Sequence, cast

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.profile import Profile, ProfileSession
from aries_cloudagent.messaging.responder import BaseResponder
from aries_cloudagent.resolver.base import (
    BaseDIDResolver,
    DIDMethodNotSupported,
    DIDNotFound,
    ResolverError,
    ResolverType,
)
from aries_cloudagent.storage.base import BaseStorage
from pydid import DID, DIDDocument
import yaml

from .acapy_tools.awaitable_handler import send_and_wait_for_response
from .protocol.v0_9 import ResolveDID, ResolveDIDResult


class DIDCommResolver(BaseDIDResolver):
    """Universal DID Resolver with DIDCOMM messages."""

    METADATA_KEY = "didcomm_resolver"
    METADATA_METHODS = "methods"

    def __init__(self):
        """Initialize DIDCommResolver."""
        super().__init__(ResolverType.NON_NATIVE)
        self._supported_methods = []

    async def setup(self, context: InjectionContext):
        """Load resolver specific configuration."""
        config_file = os.environ.get(
            "DIDCOMM_RESOLVER_CONFIG", Path(__file__).parent / "default_config.yml"
        )
        try:
            with open(config_file) as input_yaml:
                configuration = yaml.load(input_yaml, Loader=yaml.SafeLoader)
        except FileNotFoundError as err:
            raise ResolverError(
                f"Failed to load configuration file for {self.__class__.__name__}"
            ) from err
        assert isinstance(configuration, dict)
        self.configure(configuration)

    def configure(self, configuration: dict):
        """Configure this instance of the resolver from configuration dict."""
        try:
            self._supported_methods = configuration["methods"]
        except KeyError as err:
            raise ResolverError(
                f"Failed to configure {self.__class__.__name__}, "
                "missing attribute in configuration: {err}"
            ) from err

    @property
    def supported_methods(self) -> Sequence[str]:
        """Return supported methods.

        The DIDCommResolver defines a set of methods that it is willing to attempt
        to resolve. Resolver connections supported methods must be a subset of this
        list in order for the method to be resolved on a given connection.
        """
        return self._supported_methods

    @classmethod
    async def register_connection(
        cls,
        session: ProfileSession,
        connection_id: str,
        methods: Sequence[str],
    ):
        """Register connection as a resolver connection."""
        conn_record = await ConnRecord.retrieve_by_id(session, connection_id)
        conn_record = cast(ConnRecord, conn_record)
        await conn_record.metadata_set(
            session, cls.METADATA_KEY, {cls.METADATA_METHODS: methods}
        )

    def _retrieve_connection_ids(self, records: list, method: str = None):
        """Retrieve connection ids from records."""
        filtered_records = []
        for record in records:
            value = record.value
            if isinstance(value, str):
                value = json.loads(value)
            if method and method in value["methods"]:
                filtered_records.append(record)

        connection_ids = [record.tags["connection_id"] for record in filtered_records]

        if not connection_ids:
            raise DIDMethodNotSupported(
                f'No connection configured to resolve method "{method}"'
            )

        return connection_ids

    async def _resolve(self, profile: Profile, did: str) -> dict:
        """Resolve DID through remote universal resolver."""

        if not isinstance(did, str):
            did = str(did)
        method = did.split(":")[1]
        async with profile.session() as session:
            storage = session.inject(BaseStorage)

            records = await storage.find_all_records(
                ConnRecord.RECORD_TYPE_METADATA, {"key": self.METADATA_KEY}
            )
            connection_ids = self._retrieve_connection_ids(records, method)
            responder = session.inject(BaseResponder)

            for conn_id in connection_ids:
                # Construct Resolve DID message
                resolve_did_message = ResolveDID(did=did)

                try:
                    response = await send_and_wait_for_response(
                        message=resolve_did_message,
                        response_type=ResolveDIDResult,
                        responder=responder,
                        connection_id=conn_id,
                    )
                    result = response.did_document
                    if not isinstance(result, dict):
                        result = json.loads(result)
                    return result
                except DIDNotFound:
                    continue

            raise DIDNotFound("DID not found on any resolver connections")