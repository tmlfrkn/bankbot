from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Require PyJWT to avoid conflicts with deprecated 'jose' package
try:
    import jwt  # PyJWT
    if not hasattr(jwt, "encode"):
        raise ImportError("A different 'jwt' package is installed; please install PyJWT via 'pip install PyJWT' and remove conflicting packages.")
except ImportError as exc:
    raise ImportError("PyJWT is required for token operations. Install with 'pip install PyJWT'.") from exc

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from .config import settings

# ------------------------------------------------------------------------------
# Password hashing utilities (pbkdf2_sha256)
# ------------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against hashed version."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storing in the DB."""
    return pwd_context.hash(password)

# ------------------------------------------------------------------------------
# JWT helpers
# ------------------------------------------------------------------------------

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode a JWT token and return payload."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) 