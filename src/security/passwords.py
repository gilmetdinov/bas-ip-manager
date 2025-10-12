from passlib.context import CryptContext
import hashlib


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_md5_hash(plain_password: str):
    input_bytes = plain_password.encode('utf-8')
    md5_hash = hashlib.md5()
    md5_hash.update(input_bytes)
    return md5_hash.hexdigest()

