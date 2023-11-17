"""Test OOB DIDExchange Protocol."""
import pytest

from controller.controller import Controller
from controller.models import ConnRecord, ConnectionList, InvitationRecord, OobRecord
from controller.protocols import didexchange
from wrapper import AfjWrapper


@pytest.mark.asyncio
async def test_oob_didexchange(afj: AfjWrapper, acapy: Controller):
    """Test OOB DIDExchange Protocol."""
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.0"
            ],
        },
        response=InvitationRecord
    )
    inviter_conn = (
        await acapy.get(
            "/connections",
            params={"invitation_msg_id": invitation.invitation.id},
            response=ConnectionList,
        )
    ).results[0]

    await afj.receive_invitation(invitation.invitation_url)
    inviter_oob_record = await acapy.record_with_values(
        topic="out_of_band",
        record_type=OobRecord,
        connection_id=inviter_conn.connection_id,
        state="done",
    )
    inviter_conn = await acapy.record_with_values(
        topic="connections",
        record_type=ConnRecord,
        rfc23_state="request-received",
        invitation_key=inviter_oob_record.our_recipient_key,
    )
    inviter_conn = await acapy.post(
        f"/didexchange/{inviter_conn.connection_id}/accept-request",
        response=ConnRecord,
    )
    inviter_conn = await acapy.record_with_values(
        topic="connections",
        connection_id=inviter_conn.connection_id,
        rfc23_state="completed",
        record_type=ConnRecord,
    )
