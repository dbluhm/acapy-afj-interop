"""AFJ Wrapper."""

from jrpc_client import BaseSocketTransport, JsonRpcClient

class AfjWrapper:
    """AFJ Wrapper."""

    def __init__(self, transport: BaseSocketTransport, client: JsonRpcClient):
        """Initialize the wrapper."""
        self.transport = transport
        self.client = client

    async def start(self):
        """Start the wrapper."""
        await self.transport.connect()
        await self.client.start()
        await self.client.request("initialize")

    async def stop(self):
        """Stop the wrapper."""
        await self.client.stop()
        await self.transport.close()

    async def __aenter__(self):
        """Start the wrapper when entering the context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Stop the wrapper when exiting the context manager."""
        await self.stop()

    # AFJ API
    async def receive_invitation(self, invitation: str) -> dict:
        """Receive an invitation."""
        return await self.client.request("receiveInvitation", invitation=invitation)

    async def connection_state_changed(self):
        return await self.client.notification_received(
            "event.ConnectionStateChanged"
        )
