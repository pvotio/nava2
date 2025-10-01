import requests
from requests.adapters import HTTPAdapter, Retry

from ..core.config import settings

session = requests.Session()
retries = Retry(
    total=settings.REQUEST_MAX_RETRIES,
    backoff_factor=settings.REQUEST_BACKOFF_FACTOR,
    status_forcelist=[500, 502, 503, 504],
)

session.mount("http://", HTTPAdapter(max_retries=retries))
