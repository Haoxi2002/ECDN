import random

import pandas as pd

from util.entity import Request
from util.tool import URL_Generator, cal_cost


class Requester:  # 业务
    def __init__(self, id: int, app_id: str, cost_method: str, url_generator: URL_Generator):
        self.id = id
        self.app_id = app_id
        self.cost_method = cost_method
        self.url_generator = url_generator
        self.current_bandwidth = 0
        self.bandwidths = []
        self.costs = []
        self.request_nums = pd.read_csv("./data/requester_simulation.csv")['log_count_day1']

    def send_request(self, request_handler, timestamp):
        base_request_num = self.request_nums[timestamp % 86400]
        fluctuation = int(base_request_num * 0.05)  # 计算5%的波动
        request_num = base_request_num + random.randint(-fluctuation, fluctuation)  # 加上波动
        for j in range(request_num):
            request = Request(self.url_generator.get_url(), timestamp)
            response = request_handler.handle_request(request)
            self.current_bandwidth += response.content_size

    def record(self):
        self.bandwidths.append(self.current_bandwidth)
        self.current_bandwidth = 0
        self.costs.append(self.get_cost())

    def get_cost(self):
        return cal_cost(self.bandwidths, self.cost_method)


    # def get_cost(self):
    #     # 如果bandwidths长度不足8640，在前面补0
    #     if len(self.bandwidths) < 8640:
    #         padding = [0] * (8640 - len(self.bandwidths))
    #         return cal_cost(padding + self.bandwidths, self.cost_method)
    #     else:
    #         return cal_cost(self.bandwidths[-8640:], self.cost_method)




