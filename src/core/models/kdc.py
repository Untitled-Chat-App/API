from typing import TypedDict

from pydantic import BaseModel


class SignedPreKey(TypedDict):
    key_id: int
    public_key: str
    signature: str


class PreKey(TypedDict):
    key_id: int
    public_key: str


class KDCData(BaseModel):
    identity_key: str
    signed_prekey: SignedPreKey
    pre_keys: list[PreKey]
