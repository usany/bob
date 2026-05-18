import oci
 
# Initialize the client
config = oci.config.from_file()  # Uses ~/.oci/config
object_storage_client = oci.object_storage.ObjectStorageClient(config)
 
# Upload a file
namespace = 'your_namespace'  # Get from Oracle Cloud Console
bucket_name = 'your_bucket_name'
object_name = 'path/to/file.jpg'
file_path = '/local/path/to/file.jpg'
 
with open(file_path, 'rb') as f:
    object_storage_client.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        put_object_body=f
    )
