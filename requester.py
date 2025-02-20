import json
import os

from tqdm import tqdm  # 导入进度条库
import pandas as pd
from matplotlib import pyplot as plt

from util.entity import Request
from util.tool import URL_Generator, cal_cost


class Requester:  # 业务
    def __init__(self, id: int, app_id: str, cost_method: str, url_generator: URL_Generator):
        self.id = id
        self.app_id = app_id
        self.cost_method = cost_method
        self.url_generator = url_generator
        self.bw_list = {}  # 带宽列表，键为时间戳，值为该时间戳的带宽大小

    def send_request(self, request_handler):
        # # 读文件发送请求
        # request_datas = open("./data/202501200000_000_0", "r", encoding="utf-8").readlines()
        # for line in request_datas:
        #     try:
        #         data = json.loads(line)
        #         request = Request(data['req_url'], data['ts'])
        #         response = request_handler.handle_request(request)
        #         if request.timestamp not in self.bw_list:
        #             self.bw_list[request.timestamp] = 0
        #         self.bw_list[request.timestamp] += response.content_size
        #     except KeyError:
        #         # print("This request hasn't url or ts or ...")
        #         pass

        df = pd.read_csv("./data/requester_simulation.csv", index_col=0)
        for i in tqdm(range(0, 2592000, 300), desc=f"app_id: {self.app_id}"):
            request_num = df.iloc[i % 86400, i // 86400]
            for j in range(request_num):
                request = Request(self.url_generator.get_url(), i)
                response = request_handler.handle_request(request)
                if request.timestamp not in self.bw_list:
                    self.bw_list[request.timestamp] = 0
                self.bw_list[request.timestamp] += response.content_size

    def get_bw_list(self):
        bw_ls = []
        for i in range(0, 2592000, 300):
            bw_ls.append((i, self.bw_list[i] if i in self.bw_list else 0))
        return bw_ls

    def get_cost(self):
        return cal_cost([i[1] for i in self.get_bw_list()], self.cost_method)
