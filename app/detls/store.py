import os
from io import BytesIO
from google.cloud import storage


def get_from_storage(obj: str):
    bkt = storage.Client.create_anonymous_client().bucket('prism_data')
    blb = bkt.blob(obj)
    if blb.exists():
        return blb.download_as_bytes(), blb.content_type
    return None, None


def push_to_storage(obj:str, content: bytes, content_type: str = None) -> bool:
    if os.path.exists('creds.json'):
        bkt = storage.Client.from_service_account_json('creds.json').bucket('prism_data')
        blb = bkt.blob(obj)
        if blb.exists():
            blb.delete()
        blb.upload_from_file(BytesIO(content), content_type=content_type)
        return True
    return False
