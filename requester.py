import random


class Requester:  # 业务
    def __init__(self, hostname: str):
        self.hostname = hostname

    def send_request(self, path: str, request_handler):
        """随机选择路径发送请求"""
        # print(f"Requester {self.hostname} sending request for {path}")
        node_hostname, flag = request_handler.handle_request(self.hostname, path)
        return node_hostname, flag