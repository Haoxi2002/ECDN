import hashlib

from hash_ring import HashRing
from util.entity import Response, Request
from util.tool import cdn_hash


class RequestHandler:
    def __init__(self, hash_ring: HashRing):
        self.hash_ring = hash_ring
        self.fetch_from_origin_num = 0  # 回源量
        self.request_num = 0  # 请求量

    def handle_request(self, request: Request):
        """处理用户请求，分发到合适的节点"""
        fid = hashlib.md5(f"{request.url}".encode("utf-8")).hexdigest()

        # 首先尝试i=0的情况
        node = self.hash_ring.get_node(cdn_hash(fid))
        response = node.handle_request_node(request)
        if response.handle_flag:
            self.request_num += 1
            self.fetch_from_origin_num += response.fetch_flag
            return response

        # 处理i>=1的情况
        ring_length = len(self.hash_ring.ring)
        for i in range(1, ring_length):
            current_key = f"{fid}{i}"
            node = self.hash_ring.get_node(cdn_hash(current_key))
            response = node.handle_request_node(request)
            if response.handle_flag:
                self.request_num += 1
                self.fetch_from_origin_num += response.fetch_flag
                return response

        return Response(handle_flag=False)
