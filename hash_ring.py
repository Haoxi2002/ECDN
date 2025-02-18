import bisect


class HashRing:
    def __init__(self, nodes: list):
        self.ring = []  # 按哈希值排序的虚拟节点列表
        self.node_map = {}  # 哈希值到节点的映射
        for node in nodes:
            self.add_node(node)

    def add_node(self, node):
        for virtual_hash, _ in node.virtual_nodes.items():
            bisect.insort(self.ring, virtual_hash)
            self.node_map[virtual_hash] = node

    def remove_node(self, node):
        for virtual_hash in node.virtual_nodes.keys():
            if virtual_hash in self.ring:
                self.ring.remove(virtual_hash)
                del self.node_map[virtual_hash]

    def get_node(self, hash_value):
        idx = bisect.bisect_left(self.ring, hash_value)
        if idx == len(self.ring):
            idx = 0
        virtual_hash = self.ring[idx]
        return self.node_map[virtual_hash]
