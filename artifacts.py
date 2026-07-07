"""Optional S3 sync of the building-code 'artifacts' (citycodes/*.json).

This mirrors `model_loader.py` from the deployment guide. In the ML example the
artifact is a model.pkl pulled from S3; in OUR project the artifacts are the
**building-code rule files** — one JSON per jurisdiction.

Behaviour:
  * If S3_BUCKET is set (and boto3 is available) → download the city JSONs from
    S3 into citycodes/ at container startup.
  * Otherwise → silently use the files baked into the image, so the container
    runs fine with no AWS at all (great for local + the demo).

Updating a city's code in production = upload a new JSON to S3 + rolling restart,
with no image rebuild — exactly the pattern the guide uses for model weights.
"""
import os
from pathlib import Path

CODES_DIR = Path(__file__).parent / "citycodes"


def sync_city_codes() -> list[str]:
    bucket = os.environ.get("S3_BUCKET")
    prefix = os.environ.get("CITYCODES_PREFIX", "citycodes/")
    if not bucket:
        return []                       # local mode — use baked-in files
    try:
        import boto3
    except ImportError:
        print("[artifacts] boto3 not installed; using baked-in city codes")
        return []
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    CODES_DIR.mkdir(exist_ok=True)
    pulled: list[str] = []
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".json"):
            dest = CODES_DIR / Path(key).name
            s3.download_file(bucket, key, str(dest))
            pulled.append(dest.name)
    print(f"[artifacts] pulled {pulled} from s3://{bucket}/{prefix}")
    return pulled
