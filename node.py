from math import ceil

import numpy as np

from util.entity import Response, Request
from util.tool import cdn_hash, cal_cost
import time
from collections import OrderedDict


class Node:
    def __init__(self, hostname: str, cache: float, bandwidth: float, unit_price: float, cost_method: str):
        self.hostname = hostname
        self.cache_size = cache
        self.bandwidth = bandwidth
        self.unit_price = unit_price
        self.cost_method = cost_method
        self.virtual_nodes = self.generate_virtual_nodes()
        self.cache = OrderedDict()  # 使用有序字典模拟缓存，键为资源路径，值为资源大小和时间戳
        self.current_bandwidth = 0
        self.bandwidths = []
        self.costs = []
        self.rng = np.random.default_rng()

    def generate_virtual_nodes(self):
        virtual_nodes = {}
        num_virtual_nodes = ceil(self.bandwidth / 10)  # 每 10MB 对应一个虚拟节点
        for i in range(num_virtual_nodes):
            virtual_node_key = f"{self.hostname}{i}" if i != 0 else self.hostname
            virtual_node_hash = cdn_hash(virtual_node_key)
            virtual_nodes[virtual_node_hash] = self
        return virtual_nodes

    def generate_content_size(self):
        # """生成符合t分布的content_size"""
        # content_size = self.rng.standard_t(2) + 1  # 直接生成标量
        # if content_size < 0:
        #     content_size = 1
        # return content_size
        return 1

    def fetch_from_origin(self, path: str):
        """模拟回源获取数据"""
        # 模拟从源站获取的内容
        content_size = self.generate_content_size()  # 使用t分布生成新的内容大小
        current_time = time.time()  # 获取当前时间戳
        # 如果缓存已满，先清除最久未使用的项
        if len(self.cache) >= self.cache_size:
            self.cache.popitem(last=False)
        # 将新资源加入缓存
        self.cache[path] = (content_size, current_time)
        return content_size

    def get_from_cache(self, path: str):
        """获取缓存中的内容并更新时间戳"""
        if path in self.cache:
            # 获取缓存中的数据并更新时间戳
            content_size, _ = self.cache.pop(path)
            current_time = time.time()  # 获取当前时间戳
            self.cache[path] = (content_size, current_time)
            return content_size
        return None

    def handle_request_node(self, request: Request):
        """处理请求，先查缓存，缓存未命中则回源"""
        if self.current_bandwidth >= self.bandwidth:  # 带宽超限，可设置为最大带宽的百分比
            return Response(handle_flag=False)
        if self.cost_method == "C" and request.timestamp % 86400 < 72000:  # 晚高峰节点不承担非晚高峰请求
            return Response(handle_flag=False)
        content_size = self.get_from_cache(request.url)
        if content_size:
            response = Response(fetch_flag=False, content_size=content_size, handle_flag=True)
        else:
            response = Response(fetch_flag=True, content_size=self.fetch_from_origin(request.url), handle_flag=True)
        self.current_bandwidth += response.content_size
        return response

    def record(self):
        self.bandwidths.append(self.current_bandwidth)
        self.current_bandwidth = 0
        self.costs.append(self.get_cost())

    def get_cost(self):
        return cal_cost(self.bandwidths, self.cost_method, self.unit_price)
