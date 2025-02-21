import os
from math import ceil

from util.entity import Response, Request
from util.tool import cdn_hash, cal_cost

import matplotlib.pyplot as plt


class Node:
    def __init__(self, id: int, hostname: str, bandwidth: float, cost_method: str):
        self.id = id
        self.hostname = hostname
        self.bandwidth = bandwidth
        self.cost_method = cost_method
        self.virtual_nodes = self.generate_virtual_nodes()
        self.cache = {}  # 模拟缓存，键为资源路径，值为资源大小
        self.bandwidth = 0
        self.bandwidths = []
        self.costs = []

    def generate_virtual_nodes(self):
        virtual_nodes = {}
        num_virtual_nodes = ceil(self.bandwidth / 10)  # 每 10MB 对应一个虚拟节点
        for i in range(num_virtual_nodes):
            virtual_node_key = f"{self.hostname}{i}" if i != 0 else self.hostname
            virtual_node_hash = cdn_hash(virtual_node_key)
            virtual_nodes[virtual_node_hash] = self
        return virtual_nodes

    def get_from_cache(self, path: str):
        """从缓存中查找资源"""
        return self.cache.get(path)

    def fetch_from_origin(self, path: str):
        """模拟回源获取数据"""
        # 模拟从源站获取的内容
        content_size = 1  # 1MB
        self.cache[path] = content_size  # 将获取的内容加入缓存
        return content_size

    def handle_request(self, request: Request):
        """处理请求，先查缓存，缓存未命中则回源"""
        content_size = self.get_from_cache(request.url)
        response = Response()
        if not content_size:
            response.fetch_flag = True
            response.content_size = self.fetch_from_origin(request.url)
        else:
            response.content_size = content_size
        self.bandwidth += response.content_size
        return response

    def record(self):
        self.bandwidths.append(self.bandwidth)
        self.bandwidth = 0
        self.costs.append(self.get_cost())

    def get_cost(self):
        # 如果bandwidths长度不足8640，在前面补0
        if len(self.bandwidths) < 8640:
            padding = [0] * (8640 - len(self.bandwidths))
            return cal_cost(padding + self.bandwidths, self.cost_method)
        else:
            return cal_cost(self.bandwidths[-8640:], self.cost_method)