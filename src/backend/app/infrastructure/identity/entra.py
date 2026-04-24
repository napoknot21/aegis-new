from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError


class TokenValidationError(RuntimeError):
    pass


@dataclass(slots=True)
class EntraOpenIdConfiguration:
    issuer: str
    jwks_uri: str


def _build_metadata_url(authority: str) -> str:
    normalized = authority.rstrip("/")
    if normalized.endswith("/v2.0"):
        return f"{normalized}/.well-known/openid-configuration"
    return f"{normalized}/v2.0/.well-known/openid-configuration"


class EntraTokenValidator:
    def __init__(self, *, authority: str, tenant_id: str, allowed_audiences: list[str]):
        self._tenant_id = tenant_id
        self._allowed_audiences = allowed_audiences
        self._metadata_url = _build_metadata_url(authority)
        self._configuration: EntraOpenIdConfiguration | None = None
        self._jwk_client: PyJWKClient | None = None

    def _get_configuration(self) -> EntraOpenIdConfiguration:
        if self._configuration is not None:
            return self._configuration

        try:
            with urlopen(self._metadata_url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise TokenValidationError("Unable to load Microsoft Entra OpenID configuration.") from exc

        issuer = payload.get("issuer")
        jwks_uri = payload.get("jwks_uri")
        if not issuer or not jwks_uri:
            raise TokenValidationError("OpenID configuration is missing issuer or jwks_uri.")

        self._configuration = EntraOpenIdConfiguration(issuer=issuer, jwks_uri=jwks_uri)
        return self._configuration

    def _get_jwk_client(self) -> PyJWKClient:
        if self._jwk_client is None:
            configuration = self._get_configuration()
            self._jwk_client = PyJWKClient(
                configuration.jwks_uri,
                cache_keys=True,
                cache_jwk_set=True,
                lifespan=300,
                timeout=10,
            )
        return self._jwk_client

    def validate_access_token(self, token: str) -> dict[str, Any]:
        configuration = self._get_configuration()
        jwk_client = self._get_jwk_client()

        try:
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._allowed_audiences,
                issuer=configuration.issuer,
                options={"require": ["aud", "exp", "iat", "iss", "nbf"]},
            )
        except InvalidTokenError as exc:
            raise TokenValidationError("The access token could not be validated.") from exc

        if claims.get("tid") != self._tenant_id:
            raise TokenValidationError("The token tenant does not match the configured tenant.")

        if not claims.get("oid"):
            raise TokenValidationError("The token is missing the oid claim required for user resolution.")

        return claims
