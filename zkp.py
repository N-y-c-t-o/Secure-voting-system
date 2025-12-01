import hashlib

def generate_proof(secret):
    # Generate proof for the given secret
    proof = hashlib.sha256(secret.encode('utf-8')).hexdigest()
    return proof

def verify_proof(secret, proof):
    # Verify if the given proof matches the secret
    expected_proof = hashlib.sha256(secret.encode('utf-8')).hexdigest()
    return proof == expected_proof

# Example usage
secret = "MyVoteIsValid"
proof = generate_proof(secret)
is_valid = verify_proof(secret, proof)
print(f"Proof valid: {is_valid}")

