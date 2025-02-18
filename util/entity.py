class Request:
    def __init__(self, url: str, timestamp: str, ):
        self.url = url  # 请求的 URL
        self.timestamp = timestamp  # 请求的时间戳


class Response:
    def __init__(self, fetch_flag: bool = False):
        self.fetch_flag = fetch_flag  # 是否回源
        self.content_size = 0
