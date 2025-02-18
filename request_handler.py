import hashlib

import xxhash
from hash_ring import HashRing
from entity import Response


class RequestHandler:
    def __init__(self, hash_ring: HashRing, max_iterations: int = 5):
        self.hash_ring = hash_ring
        self.max_iterations = max_iterations
        self.hash_max = 2147483647

    def handle_request(self, hostname: str, path: str):
        """处理用户请求，分发到合适的节点"""
        fid = hashlib.md5(f"{path}".encode("utf-8")).hexdigest()
        fid_hash = xxhash.xxh64(fid).intdigest() % self.hash_max

        node = self.find_node(fid_hash)
        response = Response()
        if node:
            response = node.handle_request(path)
            # print(f"Request for {path} handled by {node.hostname}.")
            # print(f"Content: {content}")
        else:
            # print("Request could not be routed after maximum iterations.")
            response.fetch_flag = True
        return response

    def find_node(self, fid_hash: int):
        """根据哈希值找到节点，支持负载转移"""
        for i in range(self.max_iterations):
            node = self.hash_ring.get_node(fid_hash)
            if node:
                return node
            fid_hash = xxhash.xxh64(f"{fid_hash}{i}").intdigest() % self.hash_max
        return None
