import hashlib
import bcrypt

def verify_password(plain_password, hashed_password):
    password_bytes = plain_password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
        
    return bcrypt.checkpw(pre_hashed, hashed_password)

def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed, salt)
    return hashed.decode('utf-8')

# Test
pwd = "my_secure_password"
hashed = get_password_hash(pwd)
print(f"Hashed: {hashed}")

is_valid = verify_password(pwd, hashed)
print(f"Valid: {is_valid}")

is_invalid = verify_password("wrong_password", hashed)
print(f"Invalid correct: {not is_invalid}")

if is_valid and not is_invalid:
    print("SUCCESS: Password hashing logic verified.")
else:
    print("FAILURE: Password hashing logic failed.")
