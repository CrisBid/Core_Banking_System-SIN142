import jwt
from jose import JWTError
from fastapi import Depends, HTTPException
from datetime import datetime, timezone
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Decodifica o token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        institution_id: str = payload.get("sub")
        
        if institution_id is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verifica a validade do token
        exp = payload.get("exp")
        if datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=401,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return institution_id

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
