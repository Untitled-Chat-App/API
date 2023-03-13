from pydantic import BaseModel


class SignedPreKey(BaseModel):
    key_id: int
    public_key: str
    signature: str


class PreKey(BaseModel):
    key_id: int
    public_key: str


class KDCData(BaseModel):
    identity_key: str
    signed_prekey: SignedPreKey
    pre_keys: list[PreKey]
