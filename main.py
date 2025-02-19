import json
import os.path

import pandas as pd

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from requester import Requester
from util.tool import Hostname_Generator, URL_Generator


def main():
    setting = json.load(open('settings.json', 'r'))
    cost_methods = ['A', 'B', 'C', 'D', 'E']

    # # 初始化节点（文件读取）
    # node_file = open("./data/服务器请求量.csv", 'r')
    # df = pd.read_csv(node_file)
    #
    # nodes = [Node(hostname, eth_up_max / 1024 / 1024) for hostname, eth_up_max, _ in df.values]

    # 初始化节点（随机生成）
    node_nums = setting['node_nums']
    hostname_generator = Hostname_Generator()
    nodes = [Node(i, hostname_generator.generate(), setting['node_bandwidth'], cost_methods[i % 5]) for i in range(node_nums)]

    # 初始化哈希环
    hash_ring = HashRing(nodes)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    requesters = [Requester(i, f"app{i}", cost_methods[i], URL_Generator(f"app{i}", setting['url_num'])) for i in range(5)]

    # 业务发送请求
    for requester in requesters:
        requester.send_request(request_handler)

    print("Request Num:", request_handler.request_num)
    print("Fetch Num:", request_handler.fetch_from_origin_num)
    print("Fetch Ratio:", request_handler.fetch_from_origin_num / request_handler.request_num * 100)

    if not os.path.exists("./results"):
        os.mkdir("./results")
    if not os.path.exists("./results/csv"):
        os.mkdir("./results/csv")

    for node in nodes:
        df = pd.DataFrame(list(node.bw_list.items()), columns=['timestep', 'bandwidth'])
        df.to_csv(f"./results/csv/node_{node.id}.csv", index=False)
        if node.id < 5:
            node.draw_bw_list()

    for requester in requesters:
        df = pd.DataFrame(list(requester.bw_list.items()), columns=['timestep', 'bandwidth'])
        df.to_csv(f"./results/csv/{requester.app_id}.csv", index=False)
        requester.draw_bw_list()


if __name__ == "__main__":
    main()
