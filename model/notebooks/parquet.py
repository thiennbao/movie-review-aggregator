import polars as pl
import pyarrow.dataset as ds, pyarrow as pa
from pathlib import Path
import boto3, s3fs

SRC = Path("output_processed_json")
DST = "s3://movie-absa-lake/silver/imdb/ingest_date=2025-05-08/"

# 1. Đọc & concat
df = pl.read_ndjson(list(SRC.glob("*.json")))

# 2. Chọn & cast cột
df = (df
      .with_columns([
          pl.col("rating").cast(pl.Float64),
          pl.col("submission_date").str.to_date("%Y-%m-%d"),
          pl.col("updated_at").str.to_datetime()
      ])
     )

# 3. Viết Parquet (Snappy, row‐group 512k)
df.write_parquet(
    DST,
    compression="snappy",
    statistics=True,
    use_pyarrow=True,
    pyarrow_options={
        "filesystem": pa.fs.S3FileSystem(region="ap-southeast-1"),
        "max_rows_per_file": 250_000   # ~100 MB / file
    }
)
