from pathlib import Path
import yaml

try:  # networks that inspect HTTPS (IE Wi-Fi) break Python's CA list; fsspec then reports every S3 read as FileNotFoundError
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "config.yaml").read_text())
