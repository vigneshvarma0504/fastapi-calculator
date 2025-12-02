from app.security import hash_password, verify_password

def test_hash_and_verify_password():
    plain = "mysecretpassword"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
