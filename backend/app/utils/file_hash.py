import hashlib

def sha256_of_stream(file_storage, chunk_size=65536):
    file_storage.stream.seek(0)
    h = hashlib.sha256()
    for chunk in iter(lambda: file_storage.stream.read(chunk_size), b''):
        h.update(chunk)
    file_storage.stream.seek(0)
    return h.hexdigest()

def sha256_of_file(path, chunk_size=65536):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()