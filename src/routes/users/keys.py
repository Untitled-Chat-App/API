""" (module)
Code for the endpoint to upload and get keys
"""

__all__ = ["keys_endpoint"]

from typing import Literal

from pydantic import ValidationError
from fastapi import APIRouter, Request, Security

from core import (
    User,
    check_auth_token,
    Permissions,
    UCHTTPExceptions,
    OneTimePreKeys,
    SignedPreKeys,
    PreKeyBundle,
    KDCData,
    SignedPreKey,
    PreKey,
)

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
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_write"]
    ),
):
    user, _perms = auth_data

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
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_write"]
    ),
):
    user, _perms = auth_data

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
        except ValidationError as e:
            raise UCHTTPExceptions.INVALID_SIGNED_KEY from e

    else:
        raise UCHTTPExceptions.INVALID_KEY_TYPE(key_type)
    return {"success": True, "detail": f"Updated {key_type} successfully!"}


@keys_endpoint.get("/bundle")
async def get_user_keys(
    request: Request,
    user_id: int,
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_read"]
    ),
):
    key_owner = await User.filter(id=user_id).first()
    signed_prekey = await SignedPreKeys.filter(owner_id=user_id).first()
    prekey = await OneTimePreKeys.filter(owner_id=user_id).first()

    if signed_prekey is None or key_owner is None or prekey is None:
        raise UCHTTPExceptions.PRE_KEY_BUNDLE_FETCH_ERROR

    identity_key = key_owner.identity_key
    signed_pre_key = SignedPreKey(
        key_id=signed_prekey.id,
        public_key=signed_prekey.public_key,
        signature=signed_prekey.signature,
    )

    pre_key = PreKey(key_id=prekey.id, public_key=prekey.public_key)

    return {
        "success": True,
        "bundle": PreKeyBundle(
            user_id=str(user_id),
            identity_key=identity_key,
            signed_prekey=signed_pre_key,
            pre_key=pre_key,
        ),
    }


@keys_endpoint.get("/prekeys")
async def get_user_prekey(
    request: Request,
    key_id: int,
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_read"]
    ),
):
    prekey = await OneTimePreKeys.filter(id=key_id).first()
    if prekey is None:
        raise UCHTTPExceptions.KEY_NOT_FOUND(key_id, "prekey")

    return {
        "success": True,
        "prekey": {"id": str(prekey.id), "public_key": prekey.public_key},
    }


@keys_endpoint.post("/prekeys")
async def create_new_prekeys(
    request: Request,
    prekeys: list[PreKey],
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_write"]
    ),
):
    user, _perms = auth_data
    for prekey in prekeys:
        await OneTimePreKeys.create(
            id=prekey.key_id, public_key=prekey.public_key, owner_id=user.id
        )

    return {"success": True, "detail": "All prekeys saved!"}


@keys_endpoint.delete("/prekeys")
async def delete_prekeys(
    request: Request,
    key_id: int,
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["keys_write"]
    ),
):
    prekey = await OneTimePreKeys.filter(id=key_id).first()
    if prekey is None:
        raise UCHTTPExceptions.KEY_NOT_FOUND(key_id, "prekey")

    await prekey.delete()
    return {"success": True, "detail": "Prekey has been successfully deleted!"}
