import os

from opensearchpy import OpenSearch

OS_INDEX_NAME = os.environ.get("OS_INDEX_NAME", "dboe")

host = os.environ.get("OS_HOST", "opensearch-api.acdh-ch-dev.oeaw.ac.at")
port = os.environ.get("OS_PORT", "443")
auth = (
    os.environ.get("OS_USER", "drupal-writer"),
    os.environ.get("OS_PW", "Hansi4ever!"),
)
client = OpenSearch(
    hosts=[{"host": host, "port": port}],
    http_compress=True,
    http_auth=auth,
    use_ssl=True,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
    timeout=5,
    max_retries=0,
    retry_on_timeout=False,
)
try:
    info = client.info()
    print("Connection successful!")
    print(f"OpenSearch version: {info['version']['number']}")
    OS_CONNECTION = True
except Exception as e:
    print(f"Connection failed: {e}")
    OS_CONNECTION = False
