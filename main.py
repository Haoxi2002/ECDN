import datetime

import json
import os.path
import random

import tqdm

import pandas as pd

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator, URL_Generator


def main():
    setting = json.load(open('settings.json', 'r', encoding='utf-8'))

    # 初始化节点
    nodes = []
    hostname_generator = Hostname_Generator()
    for node_type in setting['nodes']:
        for i in range(node_type['num']):
            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=node_type['bandwidth'],
                unit_price=node_type['unit_price'],
                cost_method=node_type['cost_method'],
            ))

    # 初始化哈希环
    hash_ring = HashRing(nodes)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    businesses = []
    for business in setting['businesses']:
        businesses.append(Business(
            app_id=business['app_id'],
            unit_price=business['unit_price'],
            cost_method=business['cost_method'],
            url_num=business['url_num'],
            wave_file=business['wave_file']
        ))

    total_costs = []
    total_bandwidths = []

    # 业务发送请求
    for timestamp in tqdm.tqdm(range(0, 2592000 * 2, 300), desc="Processing timestamps"):
        for business in businesses:
            business.send_request(request_handler, timestamp)
        tot_cost = 0
        tot_bandwidth = 0
        for node in nodes:
            node.record()
            tot_cost += node.costs[-1]
            tot_bandwidth += node.bandwidths[-1]
        for business in businesses:
            business.record()
            tot_cost -= business.costs[-1]
        total_costs.append(tot_cost)
        total_bandwidths.append(tot_bandwidth)

    print("Request Num:", request_handler.request_num)
    print("Fetch Num:", request_handler.fetch_from_origin_num)
    print("Fetch Ratio:", request_handler.fetch_from_origin_num / request_handler.request_num * 100)

    if not os.path.exists("./results"):
        os.mkdir("./results")
    save_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists(f"./results/{save_time}"):
        os.mkdir(f"./results/{save_time}")

    for node in nodes:
        df = pd.DataFrame({'bandwidth': node.bandwidths, 'cost': node.costs})
        df.to_csv(f"./results/{save_time}/{node.hostname}.csv", index=False)

    for business in businesses:
        df = pd.DataFrame({'bandwidth': business.bandwidths, 'cost': business.costs})
        df.to_csv(f"./results/{save_time}/{business.app_id}.csv", index=False)

    df = pd.DataFrame({'bandwidth': total_bandwidths, 'cost': total_costs})
    df.to_csv(f"./results/{save_time}/total.csv", index=False)


if __name__ == "__main__":
    main()
