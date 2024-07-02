"""Common fixtures for tests."""

import pytest
import pytest_asyncio

from os import getenv
from wrapper import AfjWrapper
from jrpc_client import TCPSocketTransport, JsonRpcClient
from controller.controller import Controller as AcapyController

AFJ_HOST = getenv("AFJ_HOST", "localhost")
AFJ_PORT = int(getenv("AFJ_PORT", "3000"))
ACAPY = getenv("ACAPY", "http://localhost:3001")
ALICE = getenv("ALICE", "http://localhost:3002")
ROBERT = getenv("ROBERT", "http://localhost:3003")


@pytest.fixture
def transport():
    """Create a transport instance."""
    yield TCPSocketTransport(AFJ_HOST, AFJ_PORT)


@pytest.fixture
def client(transport: TCPSocketTransport):
    """Create a client instance."""
    yield JsonRpcClient(transport)


@pytest_asyncio.fixture
async def afj(client, transport):
    """Create a wrapper instance and connect to the server."""
    wrapper = AfjWrapper(transport, client)
    async with wrapper as wrapper:
        yield wrapper


@pytest_asyncio.fixture
async def acapy():
    """Create a controller instance."""
    controller = AcapyController(ACAPY)
    async with controller as controller:
        yield controller


@pytest_asyncio.fixture
async def alice():
    """Create a controller instance."""
    controller = AcapyController(ALICE)
    async with controller as controller:
        yield controller


@pytest_asyncio.fixture
async def robert():
    """Create a controller instance."""
    controller = AcapyController(ROBERT)
    async with controller as controller:
        yield controller
