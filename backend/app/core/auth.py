"""
Authentication utilities for validating Supabase JWT tokens
Uses JWKS endpoint for public key verification
"""

import jwt
import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from app.core.config import settings

security = HTTPBearer()

@lru_cache(maxsize=1)
def get_jwks():
    """
    Fetch JSON Web Key Set (JWKS) from Supabase
    Cached to avoid repeated requests
    """
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"

    try:
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch authentication keys"
        )

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify Supabase JWT token and return user info

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        dict with user_id and user_metadata

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Get JWKS (cached)
        jwks = get_jwks()

        # Decode token header to get key ID and algorithm
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        alg = unverified_header.get('alg')

        # Find matching key in JWKS
        signing_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Use appropriate algorithm based on key type
                key_type = key.get('kty')
                if key_type == 'RSA':
                    signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                elif key_type == 'EC':
                    signing_key = jwt.algorithms.ECAlgorithm.from_jwk(key)
                else:
                    raise HTTPException(
                        status_code=401,
                        detail=f"Unsupported key type: {key_type}"
                    )
                break

        if not signing_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: signing key not found"
            )

        # Verify and decode token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            audience="authenticated",
            options={"verify_exp": True}
        )

        # Extract user info
        user_id: str = payload.get("sub")
        user_metadata: dict = payload.get("user_metadata", {})

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "display_name": user_metadata.get("display_name"),
            "metadata": user_metadata
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token verification failed"
        )

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    FastAPI dependency to get current authenticated user ID

    Usage in route:
        @router.get("/endpoint")
        async def endpoint(user_id: str = Depends(get_current_user_id)):
            # user_id is now available
    """
    user_info = verify_token(credentials)
    return user_info["user_id"]

async def get_websocket_user_id(token: str) -> str:
    """
    FastAPI dependency for WebSocket authentication
    Accepts token from query parameter since WebSocket can't send headers

    Usage in WebSocket route:
        @router.websocket("/endpoint")
        async def endpoint(websocket: WebSocket, user_id: str = Depends(get_websocket_user_id)):
            # user_id is now available
    """
    class TokenCredentials:
        def __init__(self, token):
            self.credentials = token

    user_info = verify_token(TokenCredentials(token))
    return user_info["user_id"]
