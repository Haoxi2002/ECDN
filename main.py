import json

import pandas as pd

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from requester import Requester


def main():
    # 初始化节点
    node_file = open("./data/服务器请求量.csv", 'r')
    df = pd.read_csv(node_file)

    nodes = [Node(node[0], node[1] / 1024 / 1024) for node in df.values]

    # 初始化哈希环
    hash_ring = HashRing()
    for node in nodes:
        hash_ring.add_node(node)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化请求器
    requester = Requester("client1")
    request_datas = open("./data/202501200000_000_0", "r", encoding="utf-8").readlines()
    fetch_from_origin_num = 0
    for line in request_datas:
        data = json.loads(line)
        if 'req_url' in data.keys():
            hostname, flag = requester.send_request(data['req_url'], request_handler)
            fetch_from_origin_num += (flag == False)
    print("Request Num:", len(request_datas))
    print("Fetch Num:", fetch_from_origin_num)
    print("Fetch Ratio:", fetch_from_origin_num / len(request_datas) * 100)


if __name__ == "__main__":
    main()
