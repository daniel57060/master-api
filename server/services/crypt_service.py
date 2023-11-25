from passlib.context import CryptContext

crypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class CryptService:
    def hash_password(self, password):
        return crypt_context.hash(password)

    def check_password(self, password, hashed_password):
        return crypt_context.verify(password, hashed_password)


def get_crypt_service():
    return CryptService()
