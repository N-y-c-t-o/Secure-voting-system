from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import rsa

# Generate keys for RSA encryption
private_key, public_key = rsa.newkeys(512)

def encrypt_vote(vote, rsa_public_key):
    # AES encryption setup
    aes_key = get_random_bytes(16)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC)
    cipher_text = cipher_aes.encrypt(vote.ljust(32).encode('utf-8'))  # Pad to 32 bytes

    # Encrypt AES key with RSA
    cipher_rsa = PKCS1_OAEP.new(rsa_public_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    
    return encrypted_aes_key, cipher_text, cipher_aes.iv

def decrypt_vote(encrypted_aes_key, cipher_text, iv, rsa_private_key):
    # Decrypt AES key with RSA
    cipher_rsa = PKCS1_OAEP.new(rsa_private_key)
    aes_key = cipher_rsa.decrypt(encrypted_aes_key)

    # AES decryption
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted_vote = cipher_aes.decrypt(cipher_text).strip().decode('utf-8')
    
    return decrypted_vote

# Example usage
vote = "Alice"
encrypted_aes_key, cipher_text, iv = encrypt_vote(vote, public_key)
decrypted_vote = decrypt_vote(encrypted_aes_key, cipher_text, iv, private_key)
print(f"Decrypted vote: {decrypted_vote}")
