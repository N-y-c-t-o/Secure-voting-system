import rsa

# Generate keys (in real-world, you'd store private/public keys securely)
public_key, private_key = rsa.newkeys(512)

def sign_candidates(candidates):
    # Serialize candidate data and sign it
    candidates_data = ', '.join(candidates).encode('utf-8')
    signature = rsa.sign(candidates_data, private_key, 'SHA-256')
    return signature

def verify_signature(candidates, signature):
    candidates_data = ', '.join(candidates).encode('utf-8')
    try:
        rsa.verify(candidates_data, signature, public_key)
        print("Signature valid!")
        return True
    except rsa.VerificationError:
        print("Signature invalid!")
        return False

# Example usage
candidates = ['Alice', 'Bob', 'Charlie']
signature = sign_candidates(candidates)
verify_signature(candidates, signature)
