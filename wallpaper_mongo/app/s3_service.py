"""
S3 upload service.

Currently implemented as a MOCK because AWS credentials are not
available. The interface (upload_file) is designed so that swapping
in a real boto3-backed implementation later requires no changes to
calling code in the routes.
"""
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.utils import ALLOWED_IMAGE_CONTENT_TYPES, MAX_UPLOAD_FILE_SIZE_BYTES, get_logger

logger = get_logger(__name__)


class S3Service:
    """Reusable abstraction over file storage (S3 today, mocked for now)."""

    def __init__(self) -> None:
        self.bucket_name = settings.AWS_BUCKET_NAME
        self.use_mock = settings.USE_MOCK_S3

    async def upload_file(self, file: UploadFile, folder: str = "uploads") -> str:
        """
        Uploads a file and returns its publicly accessible URL.

        MOCK BEHAVIOR: validates the file then returns a deterministic
        dummy URL: https://dummy-s3-bucket.com/{folder}/{file.filename}
        """
        try:
            content = await file.read()

            if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type '{file.content_type}'.",
                )
            if len(content) > MAX_UPLOAD_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail="File is too large.")

            await file.seek(0)

            if self.use_mock:
                url = f"https://dummy-s3-bucket.com/{folder}/{file.filename}"
                logger.info("Mock S3 upload: %s -> %s", file.filename, url)
                return url

            # ----------------------------------------------------------------
            # Future real implementation (kept commented for reference):
            #
            # import boto3, uuid
            # s3_client = boto3.client(
            #     "s3",
            #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            #     region_name=settings.AWS_REGION,
            # )
            # key = f"{folder}/{uuid.uuid4()}_{file.filename}"
            # s3_client.put_object(
            #     Bucket=self.bucket_name, Key=key, Body=content,
            #     ContentType=file.content_type,
            # )
            # return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            # ----------------------------------------------------------------
            raise HTTPException(
                status_code=500, detail="Real S3 integration is not configured yet."
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("File upload failed")
            raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


def get_s3_service() -> S3Service:
    """Dependency provider for S3Service."""
    return S3Service()
