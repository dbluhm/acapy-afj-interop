"""Test OOB DIDExchange Protocol."""
import pytest

from controller.controller import Controller
from controller.logging import logging_to_stdout
from controller.models import ConnectionList, InvitationRecord, OobRecord
from wrapper import AfjWrapper


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
