import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import config
from config.redis_client import check_redis_connection
from database import database
from routes.v1 import api_v1
from utils.functions import mask_sensitive

# Configure logging for Lambda with explicit CloudWatch compatibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for CloudWatch
    ],
    force=True,  # Force reconfiguration to avoid conflicts
)
logger = logging.getLogger("handler_service")
logger.setLevel(logging.INFO)  # Explicitly set to INFO

# FastAPI app
app = FastAPI(title="Handler Service")

database.migrate_db()

app.mount("/api/v1", api_v1)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    sensitive_keys = [
        "SERPER_API_KEY",
        "TAVILY_API_KEY",
    ]

    config_vars = {}
    for attr_name in dir(config):
        # Only include properties (exclude methods and private attributes)
        if not attr_name.startswith("_") and isinstance(
            getattr(config.__class__, attr_name, None), property
        ):
            try:
                value = getattr(config, attr_name)
                # Mask sensitive values
                if attr_name in sensitive_keys:
                    value = mask_sensitive(str(value))
                config_vars[attr_name] = value
            except Exception as e:
                config_vars[attr_name] = f"Error: {str(e)}"

    return {
        "status": "ok",
        "message": "Service is running.",
        "database": {
            "status": database.check_db_connection(),
            "message": "Database connection is healthy.",
            "tables": database.list_tables(),
        },
        "redis": check_redis_connection(),
        "config": config_vars,
    }


@app.get("/migrate")
def migrate():
    """Run migrations."""
    database.migrate_db()
    return {"status": "ok", "message": "Migrations applied."}
