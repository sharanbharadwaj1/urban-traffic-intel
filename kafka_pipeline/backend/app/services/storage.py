import shutil
import json
from pathlib import Path

import boto3
from botocore.client import BaseClient

from app.core.config import Settings


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: BaseClient | None = None
        self.backend_name = "local"

    def _get_client(self) -> BaseClient | None:
        if self.settings.storage_backend.lower() != "s3":
            return None
        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=self.settings.storage_region,
                endpoint_url=self.settings.storage_endpoint_url,
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
            )
            self.backend_name = "s3"
        return self._client

    def store_file(self, job_id: str, source_path: Path) -> str:
        client = self._get_client()
        target_name = f"raw/{job_id}/{source_path.name}"
        if client is not None:
            client.upload_file(str(source_path), self.settings.storage_bucket, target_name)
            return f"s3://{self.settings.storage_bucket}/{target_name}"

        target_path = self.settings.local_storage_path / target_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        self.backend_name = "local"
        return str(target_path.resolve())

    def store_bytes(self, key: str, payload: bytes, content_type: str = "application/octet-stream") -> str:
        client = self._get_client()
        if client is not None:
            client.put_object(
                Bucket=self.settings.storage_bucket,
                Key=key,
                Body=payload,
                ContentType=content_type,
            )
            return f"s3://{self.settings.storage_bucket}/{key}"

        target_path = self.settings.local_storage_path / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(payload)
        self.backend_name = "local"
        return str(target_path.resolve())

    def store_json(self, key: str, payload: dict) -> str:
        encoded = json.dumps(payload, default=str).encode("utf-8")
        return self.store_bytes(key=key, payload=encoded, content_type="application/json")

    def local_path_for_key(self, key: str) -> Path:
        return self.settings.local_storage_path / key
