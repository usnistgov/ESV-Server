import os
import json
import string


# extract the test session or vector set id from a
# test session or vector set JSON object or from
# a URL string
def id_from(thing):
    if 'vsId' in thing: # a vector set JSON object
        id = thing['vsId']
    elif 'url' in thing: # a test session JSON object
        id = thing['url'].split('/')[-1]
    elif 'esv/v' in thing: # probably a URL string
        id = thing.split('/')[-1]
    elif '=' in thing: # probably an action
        id = thing.split('=')[1]
    else:
        id = -1
    return int(id)

def mkdir_if_not_exists(dir_name):
    if not os.path.exists(dir_name):
        print(dir_name, 'does not exist')
        os.mkdir(dir_name)
    return dir_name

# remove all non hexadecimal characters from a string
def hexonly(hexf:str):
    return ''.join(h for h in hexf if h in string.hexdigits)

# remove all non base 10 digit characters from a string
def digitonly(digf:str):
    return ''.join(d for d in digf if d in string.digits)

# Save a JSON object to <filename> in the specified directory
def saveObject(jsonObj, filename, directory='.'):
    absdir = os.path.abspath(directory)
    if not os.path.exists(absdir):
        return f"ERROR: directory {directory} does not exist"
    filepath = os.path.join(absdir, filename)
    with open(filepath, "w") as fobj:
        json.dump(jsonObj, fobj, indent=4)
    return "SUCCESS"

# Load a JSON object from <filename> in the specified directory
def loadObject(filename, directory='.'):
    absdir = os.path.abspath(directory)
    if not os.path.exists(absdir):
        return None
    filepath = os.path.join(absdir, filename)
    with open(filepath, "r") as fobj:
        jsonObj = json.load(fobj)
    return jsonObj
