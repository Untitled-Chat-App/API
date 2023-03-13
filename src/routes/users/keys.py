""" (module)
Code for the endpoint to upload and get keys
"""

__all__ = ["keys_endpoint"]

from typing import Literal

from pydantic import ValidationError
from fastapi import APIRouter, Request, Depends, HTTPException

from core import (
    User,
    check_auth_token,
    Permissions,
    OneTimePreKeys,
    SignedPreKeys,
    permcheck,
    InvalidSignedKey,
)
from core.models import KDCData, SignedPreKey, PreKey

keys_endpoint = APIRouter(
    tags=[
        "Keys",
    ],
    prefix="/api/v1/keys",
)


@keys_endpoint.post("/")
async def post_user_keys(
    request: Request,
    kdc_data: KDCData,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_write"])

    # save identity key
    await user.update_from_dict({"identity_key": kdc_data.identity_key}).save()

    # save signed pre keys
    await SignedPreKeys.create(
        id=kdc_data.signed_prekey.key_id,
        public_key=kdc_data.signed_prekey.public_key,
        signature=kdc_data.signed_prekey.signature,
        owner_id=user.id,
    )

    # save all the one time pre keys
    for prekey in kdc_data.pre_keys:
        await OneTimePreKeys.create(
            id=prekey.key_id, public_key=prekey.public_key, owner_id=user.id
        )

    return {"success": True, "detail": "all keys saved!"}


@keys_endpoint.patch("/")
async def update_user_keys(
    request: Request,
    key_type: Literal["identity_key"] | Literal["signed_prekey"],
    new_data: str | dict,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_write"])

    if key_type == "identity_key" and isinstance(new_data, str):
        await user.update_from_dict({"identity_key": new_data}).save()
    elif key_type == "signed_prekey" and isinstance(new_data, dict):
        try:
            data = SignedPreKey(**new_data)  # type: ignore
            await SignedPreKeys.create(
                id=data.key_id,
                public_key=data.public_key,
                signature=data.signature,
                owner_id=user.id,
            )
        except ValidationError:
            raise InvalidSignedKey

    else:
        raise HTTPException(
            400,
            {
                "success": False,
                "detail": "key_type given is not one of the options",
                "options": ["identity_key", "signed_prekey"],
                "given": key_type,
            },
        )
    return {"success": True, "detail": f"Updated {key_type} successfully!"}


# TODO: all bellow endpoints


@keys_endpoint.get("/")
async def get_user_keys(
    request: Request,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_read"])


@keys_endpoint.get("/prekeys/{key_id}")
async def get_user_prekey(
    request: Request,
    key_id: int,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_read"])


@keys_endpoint.post("/prekeys")
async def create_new_prekeys(
    request: Request,
    prekeys: list[PreKey],
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_write"])


@keys_endpoint.delete("/prekeys/{key_id}")
async def delete_prekeys(
    request: Request,
    key_id: int,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_write"])
