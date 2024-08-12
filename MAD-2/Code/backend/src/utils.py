from passlib.hash import bcrypt
import secrets , jwt , os
from datetime import datetime , timedelta , timezone

_JWT_KEY = os.environ.get("JWT_KEY", secrets.token_hex(11))
_SALT_KEY = os.environ.get("SALT_KEY", secrets.token_hex(11))
_JWT_EXP = os.environ.get("JWT_EXP", 3600) # in minutes default is 1 hour

def hash_password(password):
    return bcrypt(salt=_SALT_KEY , rounds = 10 , ident='2b').hash(password)

def generate_token(payload):
    final_payload = payload.copy()
    final_payload.update({"exp": datetime.now(tz=timezone.utc) + timedelta(seconds=_JWT_EXP)})
    return jwt.encode(final_payload, _JWT_KEY, algorithm="HS256") 

def check_password(password, hashed):
    return bcrypt.verify(password, hashed)

def verify_token(token):
    return jwt.decode(token, _JWT_KEY, algorithms=["HS256"] , options={"verify_exp": True , "verify_signature": True})

def get_user(request):
    token = request.cookies.get("token", '')
    return verify_token(token)