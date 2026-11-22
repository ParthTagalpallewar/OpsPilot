"""Optional bearer credentials for the shared OpsPilot API."""

import json
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, SecretStr, TypeAdapter

Role = Literal["operator", "reviewer", "webhook"]
bearer = HTTPBearer(auto_error=False)


class ClientCredential(BaseModel):
    principal: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9._@-]+$")
    role: Role
    token: SecretStr = Field(min_length=32)


class ApiAccess:
    def __init__(self, credentials: list[ClientCredential] | None = None):
        self.enabled = credentials is not None
        self.clients = {}
        for client in credentials or []:
            secret = sha256(client.token.get_secret_value().encode()).digest()
            if secret in self.clients:
                raise ValueError("API credentials must use distinct tokens")
            self.clients[secret] = (client.principal, client.role)
        if self.enabled and not self.clients:
            raise ValueError(
                "The API credentials file must contain at least one client"
            )

    @classmethod
    def from_file(cls, path: Path | None) -> "ApiAccess":
        if path is None:
            return cls()
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
            return cls(TypeAdapter(list[ClientCredential]).validate_python(entries))
        except ValueError:
            raise ValueError("Invalid OpsPilot API credentials file") from None

    def require(self, *roles: Role):
        def authenticate(
            authorization: Annotated[
                HTTPAuthorizationCredentials | None, Depends(bearer)
            ],
        ) -> str:
            if not self.enabled:
                return "local"
            if authorization is not None:
                submitted = sha256(authorization.credentials.encode()).digest()
                for digest, (principal, role) in self.clients.items():
                    if compare_digest(digest, submitted):
                        if role in roles:
                            return principal
                        raise HTTPException(403, "Credential cannot access this route")
            raise HTTPException(
                401,
                "Valid bearer credentials are required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return authenticate
