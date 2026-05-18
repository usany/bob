"""
Oracle Cloud Object Storage backend for Django.

Uses the OCI Python SDK (already installed) with instance principal or
API-key authentication. Set credentials via environment variables or
the standard ~/.oci/config file.

Environment variables (override ~/.oci/config):
    OCI_NAMESPACE      – Object Storage namespace          (required)
    OCI_BUCKET         – Bucket name                       (required)
    OCI_REGION         – OCI region identifier             (required)
    OCI_CONFIG_FILE    – Path to OCI config file           (default: ~/.oci/config)
    OCI_CONFIG_PROFILE – Profile name inside config file   (default: DEFAULT)
"""

import io
import os
from urllib.parse import urljoin

import oci
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class OracleObjectStorage(Storage):
    """Django storage backend backed by OCI Object Storage."""

    def __init__(self):
        self.namespace = getattr(settings, "ORACLE_NAMESPACE", os.environ.get("OCI_NAMESPACE"))
        self.bucket = getattr(settings, "ORACLE_BUCKET", os.environ.get("OCI_BUCKET"))
        self.region = getattr(settings, "ORACLE_REGION", os.environ.get("OCI_REGION"))

        if not all([self.namespace, self.bucket, self.region]):
            raise ValueError(
                "Oracle Object Storage requires ORACLE_NAMESPACE, ORACLE_BUCKET, "
                "and ORACLE_REGION to be set in Django settings or environment variables."
            )

        config_file = getattr(settings, "ORACLE_CONFIG_FILE", os.environ.get("OCI_CONFIG_FILE", "~/.oci/config"))
        profile = getattr(settings, "ORACLE_CONFIG_PROFILE", os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT"))

        try:
            config = oci.config.from_file(file_location=config_file, profile_name=profile)
            self.client = oci.object_storage.ObjectStorageClient(config)
        except Exception:
            # Fall back to instance principal authentication (e.g. on OCI Compute)
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            self.client = oci.object_storage.ObjectStorageClient(
                config={"region": self.region}, signer=signer
            )

        # Public URL base for pre-authenticated or public buckets
        self._base_url = getattr(
            settings,
            "ORACLE_STORAGE_URL",
            f"https://objectstorage.{self.region}.oraclecloud.com/n/{self.namespace}/b/{self.bucket}/o/",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_object_name(self, name):
        """Return the OCI object name for a given storage name."""
        media_location = getattr(settings, "ORACLE_MEDIA_LOCATION", "media")
        if media_location:
            return f"{media_location}/{name}"
        return name

    # ------------------------------------------------------------------
    # Django Storage API
    # ------------------------------------------------------------------

    def _open(self, name, mode="rb"):
        obj_name = self._get_object_name(name)
        response = self.client.get_object(self.namespace, self.bucket, obj_name)
        return File(io.BytesIO(response.data.content), name=name)

    def _save(self, name, content):
        obj_name = self._get_object_name(name)
        content.seek(0)
        self.client.put_object(
            namespace_name=self.namespace,
            bucket_name=self.bucket,
            object_name=obj_name,
            put_object_body=content,
        )
        return name

    def delete(self, name):
        obj_name = self._get_object_name(name)
        try:
            self.client.delete_object(self.namespace, self.bucket, obj_name)
        except oci.exceptions.ServiceError as e:
            if e.status != 404:
                raise

    def exists(self, name):
        obj_name = self._get_object_name(name)
        try:
            self.client.head_object(self.namespace, self.bucket, obj_name)
            return True
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return False
            raise

    def listdir(self, path):
        prefix = self._get_object_name(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        response = self.client.list_objects(
            self.namespace, self.bucket, prefix=prefix, delimiter="/"
        )
        dirs = [cp.rstrip("/").split("/")[-1] for cp in (response.data.prefixes or [])]
        files = [
            obj.name[len(prefix):]
            for obj in response.data.objects
            if obj.name != prefix
        ]
        return dirs, files

    def size(self, name):
        obj_name = self._get_object_name(name)
        response = self.client.head_object(self.namespace, self.bucket, obj_name)
        return int(response.headers.get("content-length", 0))

    def url(self, name):
        obj_name = self._get_object_name(name)
        return urljoin(self._base_url, obj_name)
