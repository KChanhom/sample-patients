import os
import hashlib
import base64

BASE_DOCUMENTS_PATH = os.path.join('..','data','documents')

def compute_hash(fileName):
    """Compute sha1 hash of the specified file"""
    m = hashlib.sha1()
    try:
        fd = open(fileName,"rb")
    except IOError:
        print ("Unable to open the file in readmode:", fileName)
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        m.update(eachLine)
    return m.hexdigest()
   
def fetch_document(pid, filename):
    path = os.path.join(BASE_DOCUMENTS_PATH, pid, filename)
    hash = compute_hash(path)
    file_size = os.path.getsize(path)
    f = open(path, 'rb')
    encoded_file_content = base64.b64encode(f.read())
    f.close()
    return {'path': path, 'hash': hash, 'size': file_size, 'base64_content': encoded_file_content}