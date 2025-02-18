import hashlib

from hash_ring import HashRing
from util.entity import Response, Request
from util.tool import cdn_hash


class RequestHandler:
    def __init__(self, hash_ring: HashRing, max_iterations: int = 5):
        self.hash_ring = hash_ring
        self.max_iterations = max_iterations
        self.fetch_from_origin_num = 0  # 回源量
        self.request_num = 0  # 请求量

    def handle_request(self, request: Request):
        """处理用户请求，分发到合适的节点"""
        fid = hashlib.md5(f"{request.url}".encode("utf-8")).hexdigest()
        fid_hash = cdn_hash(fid)

        node = self.find_node(fid_hash)
        response = Response()
        if node:
            response = node.handle_request(request)
        else:
            response.fetch_flag = True
        self.request_num += 1
        self.fetch_from_origin_num += response.fetch_flag
        return response

    def find_node(self, fid_hash: int):
        """根据哈希值找到节点，支持负载转移"""
        for i in range(self.max_iterations):
            node = self.hash_ring.get_node(fid_hash)
            if node:
                return node
            fid_hash = cdn_hash(f"{fid_hash}{i}")
        return None
