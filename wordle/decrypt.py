import base64
from Crypto.Cipher import AES
from Crypto.Hash import MD5

def openssl_key_iv(password, salt, key_len=32, iv_len=16):
    d = d_i = b''
    while len(d) < key_len + iv_len:
        d_i = MD5.new(d_i + password + salt).digest()
        d += d_i
    return d[:key_len], d[key_len:key_len+iv_len]

def decrypt_openssl(enc_b64, password):
    enc = base64.b64decode(enc_b64)
    assert enc[:8] == b'Salted__'
    salt = enc[8:16]
    key, iv = openssl_key_iv(password.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(enc[16:])
    pad_len = decrypted[-1]
    if 1 <= pad_len <= 16:
        decrypted = decrypted[:-pad_len]
    try:
        text = decrypted.decode('utf-8')
        return text
    except UnicodeDecodeError:
        return decrypted

def decrypt(encrypted, password):
    try:
        plaintext = decrypt_openssl(encrypted, password)
        return plaintext
    except Exception as e:
        pass