import os
import json
import logging
from botocore.exceptions import ClientError
import boto3

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class AppConfig:
    def __init__(self):
        self._is_local = os.getenv("ENV") == "local"
        if not self._is_local:
            self._client = boto3.client("secretsmanager", region_name="ap-southeast-2")
            self._secret_arn = os.environ["SECRET_ARN"]

    def _get_secret_value(self, key):
        if self._is_local:
            value = os.getenv(key)
            if value is None:
                logger.error(f"Environment variable {key} not found")
                raise KeyError(f"Environment variable {key} not found")
            return value
        try:
            resp = self._client.get_secret_value(SecretId=self._secret_arn)
            secret = json.loads(resp["SecretString"])
            if key not in secret:
                logger.error(f"Key {key} not found in secret")
                raise KeyError(f"Key {key} not found in secret")
            return secret[key]
        except ClientError as e:
            logger.error(f"Secrets Manager error: {e}")
            raise
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid secret: {e}")
            raise

    @property
    def DATABASE_URL(self):
        return self._get_secret_value("DATABASE_URL")

    @property
    def AWS_REGION(self):
        return self._get_secret_value("AWS_REGION")

    @property
    def AWS_BEDROCK_MODEL_ID(self):
        return self._get_secret_value("AWS_BEDROCK_MODEL_ID")

    @property
    def SERPER_API_KEY(self):
        return self._get_secret_value("SERPER_API_KEY")

    @property
    def TAVILY_API_KEY(self):
        return self._get_secret_value("TAVILY_API_KEY")

    @property
    def REDIS_HOST(self):
        return self._get_secret_value("REDIS_HOST")

    @property
    def REDIS_PORT(self):
        return self._get_secret_value("REDIS_PORT")

    @property
    def REDIS_DB(self):
        return self._get_secret_value("REDIS_DB")

    @property
    def AWS_S3_BUCKET(self):
        return self._get_secret_value("AWS_S3_BUCKET")


config = AppConfig()
