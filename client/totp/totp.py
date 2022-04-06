from cryptography.hazmat.primitives import hashes, hmac
import time
import base64

#Generates an 8-digit TOTP password from the seed path
def generate_pass(seed_path):
    #prep seed
    seed = open(seed_path).read()
    seed = seed.replace("\n", "") #remove any extra lines
    seed = base64.b64decode(seed) #Decode because TOTP seed given in base 64

    sec = int(time.time() / 30) #unix time in 30s of seconds (increments 1 every 30 seconds)
    sec = sec.to_bytes(8,'big')


    h = hmac.HMAC(seed, hashes.SHA256())

    h.update(sec)        #use unix time as HMAC message
    hex = h.finalize().hex()


    offset = int(hex[-1], 16) * 2 #take offset (last char of hex). Multiply by 2 to get to correct byte
    passw = hex[offset:offset+8]
    binary = bin(int(passw, 16))[2:].zfill(32) #Convert hex to binary


    passw = binary[1:].zfill(32) # mask first bit as 0
    passw = int(passw, 2) % 100000000 #mod 10^8 to get 8 digit passcode
    
    return str.rjust(str(passw), 8, '0') #Fill first few digits if not 8

#Generates payload for login
def login_payload(passw):

    totp = [
        {'esvVersion': '1.0'},
        {'password': passw}
    ]
    
    #totp = json.dumps(totp)

    return totp #Should return as single-line string, not JSON
