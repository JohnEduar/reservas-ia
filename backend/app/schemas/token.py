from typing import Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until the access token expires")

    model_config = {"json_schema_extra": {"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
    }}}


class TokenPayload(BaseModel):
    sub: str                              # subject: user ID as string (JWT spec requires str)
    exp: int                              # expiration: Unix timestamp
    iat: int                              # issued at: Unix timestamp
    type: Literal["access", "refresh"]   # prevents refresh tokens from being used as access tokens
