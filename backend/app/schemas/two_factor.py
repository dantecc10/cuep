from pydantic import BaseModel


class TOTPEnrollResponse(BaseModel):
    provisioning_uri: str
    secret: str


class TOTPVerifyRequest(BaseModel):
    code: str


class ChallengeResponse(BaseModel):
    challenge_id: str
    expires_at: str
    methods: list[str]


class Verify2FARequest(BaseModel):
    challenge_id: str
    code: str
    trust_device: bool = False


class ResendRequest(BaseModel):
    challenge_id: str


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
