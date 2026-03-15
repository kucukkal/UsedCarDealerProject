import requests
from config.env import BASE_URL, API_TIMEOUT


class ApiClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def set_token(self, token: str):
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })

    def post(self, path: str, **kwargs):
        return self.session.post(f"{self.base_url}{path}", timeout=API_TIMEOUT, **kwargs)

    def get(self, path: str, **kwargs):
        return self.session.get(f"{self.base_url}{path}", timeout=API_TIMEOUT, **kwargs)

    def put(self, path: str, **kwargs):
        return self.session.put(f"{self.base_url}{path}", timeout=API_TIMEOUT, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.session.delete(f"{self.base_url}{path}", timeout=API_TIMEOUT, **kwargs)