import random

import pandas as pd

from util.entity import Request
from util.tool import URL_Generator, cal_cost


class Business:  # 业务
    def __init__(self, app_id: str, unit_price: float, cost_method: str, url_num: int, wave_file: str):
        self.app_id = app_id
        self.unit_price = unit_price
        self.cost_method = cost_method
        self.url_generator = URL_Generator(app_id, url_num)
        self.request_nums = pd.read_csv(f"./data/{wave_file}")['total_bw']
        self.current_bandwidth = 0
        self.bandwidths = []
        self.costs = []

    def send_request(self, request_handler, timestamp):
        base_request_num = round(self.request_nums[timestamp % 86400 / 300] / 32)  # 每个请求大小为32MB，需要与node.py->generate_content_size()保持一致
        # fluctuation = int(base_request_num * 0.05)  # 计算5%的波动
        # request_num = base_request_num + random.randint(-fluctuation, fluctuation)  # 加上波动
        request_num = base_request_num
        for j in range(request_num):
            request = Request(self.url_generator.get_url(timestamp), timestamp)
            response = request_handler.handle_request(request)
            self.current_bandwidth += response.content_size

    def record(self):
        self.bandwidths.append(self.current_bandwidth)
        self.current_bandwidth = 0
        self.costs.append(self.get_cost())

    def get_cost(self):
        return cal_cost(self.bandwidths, self.cost_method, self.unit_price)
