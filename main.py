import json
import os.path
import tqdm
from flask import Flask, jsonify, render_template
import threading

import pandas as pd

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from requester import Requester
from util.tool import Hostname_Generator, URL_Generator

setting = json.load(open('settings.json', 'r'))

app = Flask(__name__)
# 用于存储实时数据
node_data = {
    'bandwidths': [[] for _ in range(setting['node_nums'])],
    'costs': [[] for _ in range(setting['node_nums'])]
}
requester_data = {
    'bandwidths': [[] for _ in range(5)],
    'costs': [[] for _ in range(5)]
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def get_data():
    # 只返回最近8640个数据点（一个月）
    data_length = len(node_data['bandwidths'][0])
    start_idx = max(0, data_length - 8640)

    return jsonify({
        'nodes': {
            'bandwidths': [data[start_idx:] for data in node_data['bandwidths']],
            'costs': [data[start_idx:] for data in node_data['costs']]
        },
        'requesters': {
            'bandwidths': [data[start_idx:] for data in requester_data['bandwidths']],
            'costs': [data[start_idx:] for data in requester_data['costs']]
        },
        'start_timestamp': start_idx * 300,  # 起始时间戳
        'timestamps': list(range(start_idx * 300, start_idx * 300 + 8640 * 300, 300))
    })


def main():

    # setting = json.load(open('F:\\ECDN\\ECDN2.24\\ECDN\\settings.json', 'r'))
    setting = json.load(open('settings.json'), 'r')
    cost_methods = ['A', 'B', 'C', 'D', 'E']

    # # 初始化节点（文件读取）
    # node_file = open("./data/服务器请求量.csv", 'r')
    # df = pd.read_csv(node_file)
    #
    # nodes = [Node(hostname, eth_up_max / 1024 / 1024) for hostname, eth_up_max, _ in df.values]

    # 初始化节点（随机生成）
    node_nums = setting['node_nums']
    hostname_generator = Hostname_Generator()
    nodes = [Node(i, hostname_generator.generate(), setting['node_bandwidth'], cost_methods[i % 5]) for i in
             range(node_nums)]

    # 初始化哈希环
    hash_ring = HashRing(nodes)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    requesters = [Requester(i, f"app{i}", cost_methods[i], URL_Generator(f"app{i}", setting['url_num'])) for i in
                  range(5)]

    # 业务发送请求
    for timestamp in tqdm.tqdm(range(0, 2592000 * 2, 300), desc="Processing timestamps"):
        for requester in requesters:
            requester.send_request(request_handler, timestamp)
        for i, node in enumerate(nodes):
            node.record()
            node_data['bandwidths'][i].append(node.bandwidths[-1])
            node_data['costs'][i].append(node.costs[-1])
        for i, requester in enumerate(requesters):
            requester.record()
            requester_data['bandwidths'][i].append(requester.bandwidths[-1])
            requester_data['costs'][i].append(requester.costs[-1])

    print("Request Num:", request_handler.request_num)
    print("Fetch Num:", request_handler.fetch_from_origin_num)
    print("Fetch Ratio:", request_handler.fetch_from_origin_num / request_handler.request_num * 100)

    if not os.path.exists("./results"):
        os.mkdir("./results")
    if not os.path.exists("./results/csv"):
        os.mkdir("./results/csv")

    for node in nodes:
        df = pd.DataFrame({'bandwidth': node.bandwidths, 'cost': node.costs})
        df.to_csv(f"./results/csv/node_{node.id}.csv", index=False)

    for requester in requesters:
        df = pd.DataFrame({'bandwidth': requester.bandwidths, 'cost': requester.costs})
        df.to_csv(f"./results/csv/{requester.app_id}.csv", index=False)


if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000}).start()
    main()
