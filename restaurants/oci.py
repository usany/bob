import oci
from django.core.files.storage import Storage
from django.conf import settings
 
class OracleObjectStorage(Storage):
    def __init__(self):
        config = oci.config.from_file()
        self.client = oci.object_storage.ObjectStorageClient(config)
        self.namespace = settings.ORACLE_NAMESPACE
        self.bucket = settings.ORACLE_BUCKET
    
    def _save(self, name, content):
        self.client.put_object(
            namespace_name=self.namespace,
            bucket_name=self.bucket,
            object_name=name,
            put_object_body=content
        )
        return name
    
    def url(self, name):
        return f"https://objectstorage.{settings.ORACLE_REGION}.oraclecloud.com/n/{self.namespace}/b/{self.bucket}/o/{name}"
    
    def exists(self, name):
        try:
            self.client.get_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket,
                object_name=name
            )
            return True
        except:
            return False
