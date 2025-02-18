from entity import Request


class Requester:  # 业务
    def __init__(self, hostname: str):
        self.hostname = hostname

    def send_request(self, request: Request, request_handler):
        """随机选择路径发送请求"""
        # print(f"Requester {self.hostname} sending request for {path}")
        response = request_handler.handle_request(request)
        return response
