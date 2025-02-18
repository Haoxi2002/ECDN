from math import floor

import xxhash

from entity import Response, Request


class Node:
    def __init__(self, hostname: str, bandwidth: float):
        self.hostname = hostname
        self.bandwidth = bandwidth
        self.hash_max = 2147483647
        self.virtual_nodes = self.generate_virtual_nodes()
        self.cache = {}  # 模拟缓存，键为资源路径，值为资源内容

    def generate_virtual_nodes(self):
        virtual_nodes = {}
        num_virtual_nodes = floor(self.bandwidth // 10)  # 每 10MB 对应一个虚拟节点
        for i in range(num_virtual_nodes):
            virtual_node_key = f"{self.hostname}{i}" if i != 0 else self.hostname
            virtual_node_hash = xxhash.xxh64(virtual_node_key).intdigest() % self.hash_max
            virtual_nodes[virtual_node_hash] = self
        return virtual_nodes

    def get_from_cache(self, path: str):
        """从缓存中查找资源"""
        return self.cache.get(path)

    def fetch_from_origin(self, path: str):
        """模拟回源获取数据"""
        # print(f"Node {self.hostname}: Fetching {path} from origin...")
        # 模拟从源站获取的内容
        content_size = 1  # 1MB
        self.cache[path] = content_size  # 将获取的内容加入缓存
        return content_size

    def handle_request(self, request: Request):
        """处理请求，先查缓存，缓存未命中则回源"""
        content = self.get_from_cache(request.url)
        response = Response()
        if not content:
            response.fetch_flag = True
            response.content_size = self.fetch_from_origin(request.url)
        return response
