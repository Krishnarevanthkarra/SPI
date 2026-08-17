from jose import JWTError, jwt
from fastapi import HTTPException, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
from ..settings import settings
from .. import schemas
from datetime import datetime, timedelta

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {
            "exp": expire,
            "sessionid": data.get("sessionid"),
            "userid": data.get("userid"),
        }
    )

    encode_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


def verify_access_token(token: str):

    try:

        payload = jwt.decode(token, key=SECRET_KEY, algorithms=ALGORITHM)
        userid = payload.get("userid")
        if userid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = schemas.TokenBody(
            sessionid=payload.get("sessionid"), userid=payload.get("userid")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def get_current_user(token=Depends(oauth2_scheme)):

    token = verify_access_token(token)
    return {"userid": token.userid}
