from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password
)

password = "admin123"

# Hash password
hashed = hash_password(password)
print("HASH:", hashed)

# Verify password
is_valid = verify_password(password, hashed)
print("PASSWORD VALID:", is_valid)

# Create token
token = create_access_token({"sub": "admin@test.com"})
print("TOKEN:", token)

# Decode token
decoded = decode_token(token)
print("DECODED:", decoded)