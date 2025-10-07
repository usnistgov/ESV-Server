from cryptography.hazmat.primitives import hashes, hmac
import time
import base64

def convert_to_ascii(convert):
     for x in convert:
        if f"'{x}'" == ascii(x):
            pass
        else:
            convert = convert.replace(x, "")
     return convert

def get_current_window():
    return int(time.time() / 30)

# Generates an 8-digit TOTP password from the seed path
def generate_pass(seed_path):

    # prep seed
    seed = open(seed_path).read()
    seed = convert_to_ascii(seed)                 # Added because "invisible" non-ASCII characters like Byte Order Mark were causing chaos
    seed = seed.replace("\n", "")               # Remove any extra lines
    seed = base64.b64decode(seed)               # Decode because TOTP seed given in base 64

    sec = get_current_window()                  # Unix time in 30s of seconds (increments 1 every 30 seconds)
    sec = sec.to_bytes(8,'big')

    h = hmac.HMAC(seed, hashes.SHA256())

    h.update(sec)                               # Use unix time as HMAC message
    hex = h.finalize().hex()

    offset = int(hex[-1], 16) * 2               # Take offset (last char of hex). Multiply by 2 to get to correct byte
    passw = hex[offset:offset+8]
    binary = bin(int(passw, 16))[2:].zfill(32)  # Convert hex to binary

    passw = binary[1:].zfill(32)                # Mask first bit as 0
    passw = int(passw, 2) % 100000000           # mod 10^8 to get 8 digit passcode
    
    return str.rjust(str(passw), 8, '0')        # Pad to 8 characters

def is_totp_expired(response):
    if int(response.status_code) != 403:
        return False
    
    responseJson = response.json()
    errorMsg = responseJson[1]["error"]

    if "totp" in errorMsg.lower() and "window" in errorMsg.lower():
        return True
    
    return False

def did_totp_fail(response):
    if int(response.status_code) != 403:
        return False
    
    responseJson = response.json()
    errorMsg = responseJson[1]["error"]

    if "totp" in errorMsg.lower() and "failed" in errorMsg.lower():
        return True
    
    return False