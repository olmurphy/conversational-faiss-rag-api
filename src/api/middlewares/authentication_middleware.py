import json
import logging
from typing import Callable

import jwt
from context import AppContext
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from api.middlewares.logger_middleware import SESSION_ID_HEADER


exclude_paths = ["/documentation", "/docs", "/openapi.json", "/readiness", "/liveness", "/favicon.ico"]

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate incoming requests using JWT and JWKS.

    This middleware intercepts incoming requests, extracts the authentication token
    (either from the Authorization header or Redis session), validates it against
    a JWKS, and allows or denies access based on the validation result.

    JWT (JSON Web Token):
        - A compact, URL-safe means of representing claims to be transferred between
          two parties.
        - Used here to carry user authentication information.

    JWKS (JSON Web Key Set):
        - A set of public keys used to verify the signature of a JWT.
        - Obtained from the issuer's public keys endpoint.
        - Keys are cached in Redis to improve performance.

    Procedure:
        1. Extract the token from the Authorization header or Redis session.
        2. If no token is found, return a 401 Unauthorized error.
        3. Extract the 'kid' (Key ID) from the token header.
        4. Extract the 'iss' (Issuer) from the token payload.
        5. Construct the JWKS URL using the issuer.
        6. Retrieve the JWKS from Redis cache or fetch it from the URL.
        7. Find the matching key in the JWKS using the 'kid'.
        8. If no matching key is found, return a 401 Unauthorized error.
        9. Decode the token using the public key from the JWKS, verifying the signature,
           audience, and issuer.
        10. If the token is valid, proceed with the request.
        11. If any error occurs during the process, return a 401 or 500 error.
    """
    def __init__(self, app: FastAPI, app_context: AppContext):
        super().__init__(app)
        self.logger: logging.Logger = app_context.logger
        self.redis_auth = app_context.redis_auth
        if not self.redis_auth:
            raise ValueError("RedisAuth is not initialized in the context")

    async def dispatch(self, request: Request, call_next: Callable):
        self.logger.debug({"message": f"AuthenticationMiddleware: Intercepting request {request.method} {request.url.path}"})
        if any(request.url.path.startswith(path) for path in exclude_paths):
            self.logger.debug(f"Excluded path: {request.url.path}")
            return await call_next(request)
        

        # Try to get token from Authorization header first
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            self.logger.debug({"message": "Token found in Authorization header"})
        else:
            # If no Authorization header, try session id from redis
            self.logger.debug({"message": "No Authorization header found, checking session id"})
            session_id = request.headers.get(SESSION_ID_HEADER)
            if session_id:
                token = self.redis_auth.get_access_token(session_id=session_id)

        if not token:
            self.logger.warning({"message": "No valid authentication token found"})
            raise HTTPException(
                status_code=401, detail="No valid authentication token found"
            )

        try:
            await self.authenticate_request(token)
            response = await call_next(request)
            self.logger.debug({"message": f"Request {request.method} {request.url.path} Authentication successful"})
            return response
        except HTTPException as e:
            self.logger.warning({"message": "Authentication error", "error": e})
            raise e
        except Exception as e:
            self.logger.error({"message": "Unexpected error during authentication", "error": e})
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def authenticate_request(self, token: str):
        self.logger.debug({"message": "Authenticating request with token", "data": token})
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]
        unverified_payload = jwt.decode(
            token, algorithms=["RS256"], options={"verify_signature": False}
        )

        issuer = unverified_payload["iss"]
        jwks_url = issuer + "/publickeys"
        audience = unverified_payload["aud"][0]

        self.logger.debug({"message": "Fetching JWKS URL", "data": jwks_url})
        jwks = self.redis_auth.get_jwks(jwks_url)
        matching_keys = [key for key in jwks["keys"] if key["kid"] == kid]

        if not matching_keys:
            self.logger.warning({"message": "Invalid KID or JWKS not found"})
            raise HTTPException(status_code=401, detail="Invalid KID or JWKS not found")

        key = matching_keys[0]
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

        try:
            jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
            )
            self.logger.debug({"message": "Token successfully validated"})
        except jwt.ExpiredSignatureError:
            self.logger.warning({"message": "Token has expired"})
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidAudienceError:
            self.logger.warning({"message": "Invalid audience"})
            raise HTTPException(status_code=401, detail="Invalid audience")
        except jwt.InvalidIssuerError:
            self.logger.warning({"message": "Invalid issuer"})
            raise HTTPException(status_code=401, detail="Invalid issuer")
        except jwt.InvalidSignatureError:
            self.logger.warning({"message": "Invalid token signature"})
            raise HTTPException(status_code=401, detail="Invalid token signature")
        except jwt.PyJWTError as e:
            self.logger.error({"message": "JWT error", "error": e})
            self.logger.error(f"JWT error: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
