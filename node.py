from math import ceil

from util.entity import Response, Request
from util.tool import cdn_hash, cal_cost
import time
from collections import OrderedDict
from scipy.stats import t


class Node:
    def __init__(self, id: int, hostname: str, bandwidth: float, cost_method: str):
        self.id = id
        self.hostname = hostname
        self.bandwidth = bandwidth
        self.cost_method = cost_method
        self.virtual_nodes = self.generate_virtual_nodes()
        # self.cache = {}  # 模拟缓存，键为资源路径，值为资源大小
        self.cache = OrderedDict()  # 使用有序字典模拟缓存，键为资源路径，值为资源大小和时间戳
        self.current_bandwidth = 0
        self.bandwidths = []
        self.costs = []
        self.capacity = 10  # 最大缓存容量

    def generate_virtual_nodes(self):
        virtual_nodes = {}
        num_virtual_nodes = ceil(self.bandwidth / 10)  # 每 10MB 对应一个虚拟节点
        for i in range(num_virtual_nodes):
            virtual_node_key = f"{self.hostname}{i}" if i != 0 else self.hostname
            virtual_node_hash = cdn_hash(virtual_node_key)
            virtual_nodes[virtual_node_hash] = self
        return virtual_nodes

    # def get_from_cache(self, path: str):
    #     """从缓存中查找资源"""
    #     return self.cache.get(path)
    #
    # def fetch_from_origin(self, path: str):
    #     """模拟回源获取数据"""
    #     # 模拟从源站获取的内容
    #     content_size = 1  # 1MB
    #     self.cache[path] = content_size  # 将获取的内容加入缓存
    #     return content_size

    def _evict(self):
        """当缓存超过最大容量时，移除最久未使用的项"""
        self.cache.popitem(last=False)  # 删除最久未使用的项（即最前面那个）

    def generate_content_size(self):
        """生成符合t分布的content_size"""
        df = 2  # 设置自由度
        content_size_t = t.rvs(df, size=1)[0]  # 生成符合t分布的随机数
        content_size = content_size_t + 1  # 调整为1MB为中心
        if content_size < 0:
            content_size = 1  # 如果生成的大小小于0，设置为1MB
        return content_size

    def fetch_from_origin(self, path: str):
        """模拟回源获取数据"""
        # 如果缓存中已有资源，直接返回缓存的大小，无需再次模拟，并更新时间戳
        if path in self.cache:
            content_size, _ = self.cache.pop(path)  # 删除原有的资源
            current_time = time.time()  # 获取当前时间戳
            # 将该资源重新插入并更新它的时间戳
            self.cache[path] = (content_size, current_time)
            return content_size

        # 模拟从源站获取的内容
        content_size = self.generate_content_size()  # 使用t分布生成新的内容大小
        current_time = time.time()  # 获取当前时间戳
        # 如果缓存已满，先清除最久未使用的项
        if len(self.cache) >= self.capacity:
            self._evict()

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

    def handle_request(self, request: Request):
        """处理请求，先查缓存，缓存未命中则回源"""
        content_size = self.get_from_cache(request.url)
        response = Response()
        if not content_size:
            response.fetch_flag = True
            response.content_size = self.fetch_from_origin(request.url)
        else:
            response.content_size = content_size
        self.current_bandwidth += response.content_size
        return response

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


