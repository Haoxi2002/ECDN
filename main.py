import pandas as pd

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from requester import Requester
from util.tool import Hostname_Generator


def main():
    cost_methods = ['A', 'B', 'C', 'D', 'E']

    # # 初始化节点（文件读取）
    # node_file = open("./data/服务器请求量.csv", 'r')
    # df = pd.read_csv(node_file)
    #
    # nodes = [Node(hostname, eth_up_max / 1024 / 1024) for hostname, eth_up_max, _ in df.values]

    # 初始化节点（随机生成）
    node_nums = 100
    hostname_generator = Hostname_Generator()
    nodes = [Node(i, hostname_generator.generate(), 1024, cost_methods[i % 5]) for i in range(node_nums)]

    # 初始化哈希环
    hash_ring = HashRing(nodes)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    requesters = [Requester(i, "client1", cost_methods[i]) for i in range(5)]

    # 业务发送请求
    for requester in requesters:
        requester.send_request(request_handler)

    print("Request Num:", request_handler.request_num)
    print("Fetch Num:", request_handler.fetch_from_origin_num)
    print("Fetch Ratio:", request_handler.fetch_from_origin_num / request_handler.request_num * 100)


if __name__ == "__main__":
    main()
