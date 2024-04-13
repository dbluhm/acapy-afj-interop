"""Test OOB DIDExchange Protocol."""
from typing import Optional
import pytest

from controller.controller import Controller
from controller.logging import logging_to_stdout
from controller.models import ConnRecord, DIDResult, InvitationMessage, InvitationRecord, OobRecord
from controller.protocols import _make_params
from wrapper import AfjWrapper

logging_to_stdout()


@pytest.mark.asyncio
async def test_resolution(afj: AfjWrapper):
    """Test DID Resolution."""
    logging_to_stdout()
    await afj.resolve(
        "did:peer:4zQmPChMGtfYbemhdD39WccouAgv8pRBckYxVKZMUQTpSrNm:z2eXLFxcARVttUb745a1edZtQXpgfHxkii7sVmK1SQrSbSNZ7KYetf62U2FxJfWimfrzBzVBNc7JyQFtvcN7WNBuqdoNzq97DyyaQW8cWbz42sZEVtJyUcFw9J251Lsm6izx5Tiak6aDtkBNCBFMLMVJ155cXT7NRJ9LLaQMLhcNd3U9442q1f3VNaDvm59XnE5LCSk1B3uD179wPeXDfqFee7jQNakCPHQBADX2egstJKReawJ6S6fRSKcXm89uomdhCDizAV7KTMSxTos6RkgrFugzP3vqRuUkmnPYb2VnQPGMn46eThNoMMf6q7dbGpvTVne6J5E6qK4HsJco5pEHWT9rWMYR88fWHbrNJPx1sAye5TtjP5mjJg9g4kCJmsYNxShdoT7vKjFLXDGWSMmvcVKBAN4Cu41y7sDtz7uLagW6LPK6E4wa26K1pkTvEgV1sCKzgtdwTS5ggCSXAb5Uf6sDqH18Qw8TDa62YtiPzoNrmWiaFDrzjme"
    )
    await afj.resolve(
        "did:peer:2.Vz6Mkh95XxQsoAvJBrDUc6UfuwjTZZaeuPzPVDoK76EpwCpQ9.SeyJpZCI6IiNkaWRjb21tLTAiLCJ0IjoiZGlkLWNvbW11bmljYXRpb24iLCJwcmlvcml0eSI6MCwicmVjaXBpZW50S2V5cyI6WyIja2V5LTEiXSwiciI6W10sInMiOiJodHRwOi8vYWNhcHk6MzAwMCJ9"
    )


@pytest.mark.asyncio
async def test_oob_didexchange(afj: AfjWrapper, acapy: Controller):
    """Test OOB DIDExchange Protocol."""
    logging_to_stdout()
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
        },
        response=InvitationRecord
    )
    inviter_conn = (
        await acapy.get(
            "/connections",
            params={"invitation_msg_id": invitation.invitation.id},
        )
    )["results"][0]

    await afj.receive_invitation(invitation.invitation_url)
    inviter_oob_record = await acapy.record_with_values(
        topic="out_of_band",
        record_type=OobRecord,
        connection_id=inviter_conn["connection_id"],
        state="done",
    )
    inviter_conn = await acapy.record_with_values(
        topic="connections",
        rfc23_state="request-received",
        invitation_key=inviter_oob_record.our_recipient_key,
        timeout=10,
    )
    conn_id = inviter_conn["connection_id"]
    inviter_conn = await acapy.post(
        f"/didexchange/{conn_id}/accept-request",
    )
    inviter_conn = await acapy.record_with_values(
        topic="connections",
        connection_id=conn_id,
        rfc23_state="completed",
    )


async def didexchange(
    inviter: Controller,
    invitee: Controller,
    *,
    invite: InvitationMessage,
    use_existing_connection: bool = False,
    use_did_method: Optional[str] = None,
    use_did: Optional[str] = None,
):
    invitee_oob_record = await invitee.post(
        "/out-of-band/receive-invitation",
        json=invite,
        params=_make_params(
            use_existing_connection=use_existing_connection,
        ),
        response=OobRecord,
    )
    invitee_conn = await invitee.post(
        f"/didexchange/{invitee_oob_record.connection_id}/accept-invitation",
        params=_make_params(use_did=use_did, use_did_method=use_did_method),
        response=ConnRecord,
    )
    inviter_oob_record = await inviter.record_with_values(
        topic="out_of_band",
        invi_msg_id=invite.id,
        state="done",
        record_type=OobRecord,
    )
    inviter_conn = await inviter.record_with_values(
        topic="connections",
        record_type=ConnRecord,
        rfc23_state="request-received",
        invitation_key=inviter_oob_record.our_recipient_key,
    )
    inviter_conn = await inviter.post(
        f"/didexchange/{inviter_conn.connection_id}/accept-request",
        response=ConnRecord,
    )

    await invitee.record_with_values(
        topic="connections",
        connection_id=invitee_conn.connection_id,
        rfc23_state="response-received",
    )
    invitee_conn = await invitee.record_with_values(
        topic="connections",
        connection_id=invitee_conn.connection_id,
        rfc23_state="completed",
        record_type=ConnRecord,
    )
    inviter_conn = await inviter.record_with_values(
        topic="connections",
        connection_id=inviter_conn.connection_id,
        rfc23_state="completed",
        record_type=ConnRecord,
    )
    return inviter_conn, invitee_conn


@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_no_use_did_method(acapy: Controller, alice: Controller):
    """Test DIDExchange between Acapy and Alice."""
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation)
    assert alice_conn.my_did and alice_conn.my_did.startswith("did:peer:4")
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:4")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_use_2(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:2")
    assert alice_conn.my_did and alice_conn.my_did.startswith("did:peer:2")
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:2")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_use_4(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:4")
    assert alice_conn.my_did and alice_conn.my_did.startswith("did:peer:4")
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:4")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_0_use_2_overridden(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.0"
            ],
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:2")
    assert alice_conn.my_did and not alice_conn.my_did.startswith("did:")
    assert acapy_conn.my_did and not acapy_conn.my_did.startswith("did:")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_0_use_4_overridden(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.0"
            ],
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:4")
    assert alice_conn.my_did and not alice_conn.my_did.startswith("did:")
    assert acapy_conn.my_did and not acapy_conn.my_did.startswith("did:")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_use_did(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
        },
        response=InvitationRecord
    )
    result = (await alice.post(
        "/wallet/did/create",
        json={
            "method": "did:peer:4"
        },
        response=DIDResult
    )).result
    assert result
    alice_did = result.did
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did=alice_did)
    # Stored DID on conn rec is short form
    assert alice_conn.my_did and alice_did.startswith(alice_conn.my_did)
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:4")

@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_invite_use_did(acapy: Controller, alice: Controller):
    result = (await acapy.post(
        "/wallet/did/create",
        json={
            "method": "did:peer:4"
        },
        response=DIDResult
    )).result
    assert result
    acapy_invite_did = result.did
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
            "use_did": acapy_invite_did
        },
        response=InvitationRecord
    )
    assert invitation.invitation.services and invitation.invitation.services[0] == acapy_invite_did
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:2")
    assert alice_conn.my_did and alice_conn.my_did.startswith("did:peer:2")
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:2")


@pytest.mark.asyncio
async def test_acapy_to_alice_1_1_invite_use_4(acapy: Controller, alice: Controller):
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
            "use_did_method": "did:peer:4",
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:4")
    assert alice_conn.my_did and alice_conn.my_did.startswith("did:peer:4")
    assert acapy_conn.my_did and acapy_conn.my_did.startswith("did:peer:4")
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1"
            ],
            "use_did_method": "did:peer:4",
        },
        response=InvitationRecord
    )
    acapy_conn, alice_conn = await didexchange(acapy, alice, invite=invitation.invitation, use_did_method="did:peer:4")

@pytest.mark.asyncio
async def test_acapy_to_robert(acapy: Controller, robert: Controller):
    """Test DIDExchange between Acapy and Alice."""
    invitation = await acapy.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.1",
                "https://didcomm.org/didexchange/1.0",
            ],
        },
        response=InvitationRecord
    )
    await didexchange(acapy, robert, invite=invitation.invitation)
    invitation = await robert.post(
        "/out-of-band/create-invitation",
        json={
            "handshake_protocols": [
                "https://didcomm.org/didexchange/1.0",
            ],
        },
        response=InvitationRecord
    )
    await didexchange(robert, acapy, invite=invitation.invitation)
