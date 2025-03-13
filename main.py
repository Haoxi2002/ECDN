import json
import os.path
import random

import tqdm
from flask import Flask, jsonify, render_template, request
import threading

import pandas as pd

import time

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from requester import Requester
from util.tool import Hostname_Generator, URL_Generator

# setting = json.load(open('settings.json', 'r'))
setting = json.load(open('F:\\ECDN\\ECDN2.24\\ECDN\\settings.json', 'r'))

app = Flask(__name__)
# 用于存储实时数据
# node_data = {
#     'bandwidths': [[] for _ in range(setting['node_nums'])],
#     'costs': [[] for _ in range(setting['node_nums'])]
# }

# **动态初始化 node_data**
node_data = {
    "node_A": {
        'bandwidths': [[] for _ in range(setting["node_A"]["node_num"])],
        'costs': [[] for _ in range(setting["node_A"]["node_num"])]
    },
    "node_B": {
        'bandwidths': [[] for _ in range(setting["node_B"]["node_num"])],
        'costs': [[] for _ in range(setting["node_B"]["node_num"])]
    }
}


requester_data = {
    'bandwidths': [[] for _ in range(setting['requester_nums'])],
    'costs': [[] for _ in range(setting['requester_nums'])]
}
total_cost_data = []  # 添加总成本数据数组
total_bandwidth_data = []  # 添加总带宽数据数组

# 全局存储用户输入的参数
unit_price = None
url_num = None
bandwidth_num = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def get_data():
    # **防止数据为空导致访问错误**
    if not node_data["node_A"]["bandwidths"] or not node_data["node_B"]["bandwidths"]:
        return jsonify({"error": "No bandwidth data available"}), 500

    data_length = len(node_data["node_A"]["bandwidths"][0])  # 获取 node_A 第一个节点的数据长度
    start_idx = max(0, data_length - 8640)

    return jsonify({
        'nodes': {
            'bandwidths': {
                "node_A": [data[start_idx:] for data in node_data["node_A"]['bandwidths']],
                "node_B": [data[start_idx:] for data in node_data["node_B"]['bandwidths']]
            },
            'costs': {
                "node_A": [data[start_idx:] for data in node_data["node_A"]['costs']],
                "node_B": [data[start_idx:] for data in node_data["node_B"]['costs']]
            }
        },
        'requesters': {
            'bandwidths': [data[start_idx:] for data in requester_data['bandwidths']],
            'costs': [data[start_idx:] for data in requester_data['costs']]
        },
        'total_cost': total_cost_data[start_idx:],
        'total_bandwidth': total_bandwidth_data[start_idx:],
        'start_timestamp': start_idx * 300,
        'timestamps': list(range(start_idx * 300, start_idx * 300 + 8640 * 300, 300))
    })

@app.route('/update_params', methods=['POST'])
def update_params():
    global unit_price, url_num, bandwidth_num

    # 从前端接收数据
    data = request.get_json()

    # 获取用户输入的参数
    unit_price = data.get('unit_price', None)
    url_num = data.get('url_num', None)
    bandwidth_num = data.get('bandwidth_num', None)

    # 检查参数是否有效
    if unit_price is not None and url_num is not None and bandwidth_num is not None:
        return jsonify({"status": "success", "message": "Parameters received"})
    else:
        return jsonify({"status": "error", "message": "Missing parameters"})

def main():

    global unit_price, url_num, bandwidth_num

    # 等待直到参数被接收后才能开始模拟
    while unit_price is None or url_num is None or bandwidth_num is None:
        print("Waiting for parameters to be set...")
        time.sleep(5)

    cost_methods = ['A', 'B', 'C', 'D', 'E']

    # 能输入单价，增加unit_price
    unit_price = [1, 1, 1, 100, 1]

    # 能输入带宽和请求总量，增加url_num和bandwidth_num
    url_num = 10000
    bandwidth_num = 10000

    # # 初始化节点（随机生成）
    # node_nums = setting['node_nums_total']
    # hostname_generator = Hostname_Generator()
    # nodes = [Node(i, hostname_generator.generate(), setting['node_bandwidth'], cost_methods[i % 5],
    #               round(bandwidth_num / url_num, 2)) for i in range(node_nums)]

    # **获取节点总数**
    node_nums = setting['node_nums_total']
    hostname_generator = Hostname_Generator()

    # **读取所有节点类型（动态获取）**
    node_types = {key: value for key, value in setting.items() if key.startswith("node_") and key != "node_nums_total"}

    # **检查总数是否匹配**
    total_node_count = sum(node_info["node_num"] for node_info in node_types.values())
    if total_node_count != node_nums:
        raise ValueError(f"Mismatch: total nodes {node_nums}, but sum of node types {total_node_count}")

    # **随机分配节点**
    node_ids = list(range(node_nums))
    random.shuffle(node_ids)  # **打乱节点 ID 顺序**

    nodes = []
    index = 0

    # **遍历所有节点类型，并按数量分配**
    node_type_assignments = {}
    for node_type, node_info in node_types.items():
        node_num = node_info["node_num"]
        node_bandwidth = node_info["node_bandwidth"]

        assigned_ids = set(node_ids[index: index + node_num])  # **从打乱的 ID 列表中选出该类型的节点**
        node_type_assignments[node_type] = assigned_ids
        index += node_num  # **更新索引，确保不会重复分配**

    # **创建节点**
    for i in range(node_nums):
        node_type = next(nt for nt, ids in node_type_assignments.items() if i in ids)  # **查找该节点属于哪个类型**
        node_bandwidth = node_types[node_type]["node_bandwidth"]  # **获取对应的带宽**

        node = Node(
            id=i,
            hostname=hostname_generator.generate(),
            bandwidth=node_bandwidth,  # **使用动态带宽**
            cost_method=cost_methods[i % len(cost_methods)],  # **支持动态 cost 方法**
            content_size=round(bandwidth_num / url_num, 2)
        )
        node.type = node_type  # **赋值 type**
        nodes.append(node)

    # **输出每个节点的 ID 和类型**
    print("\n===== Node Assignments =====")
    for node in nodes:
        print(f"Node ID: {node.id}, Type: {node.type}, Bandwidth: {node.bandwidth}")

    # 初始化哈希环
    hash_ring = HashRing(nodes)

    # 初始化请求处理器
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    # requesters = [Requester(i, f"app{i}", cost_methods[i], URL_Generator(f"app{i}", setting['url_num'])) for i in [0, 1, 4]]
    requesters = [Requester(i, f"app{i}", cost_methods[i], URL_Generator(f"app{i}", url_num)) for i in [0, 1, 4]]

    # 业务发送请求
    for timestamp in tqdm.tqdm(range(0, 2592000 * 2, 300), desc="Processing timestamps"):
        for requester in requesters:
            requester.send_request(request_handler, timestamp)
        tot_cost = 0
        tot_bandwidth = 0
        for node in nodes:
            node.record(unit_price)
            # **获取该节点在 `node_type` 里的索引**
            node_index = node.id % setting[node.type]['node_num']
            # **存储带宽和成本**
            node_data[node.type]['bandwidths'][node_index].append(node.bandwidths[-1])
            node_data[node.type]['costs'][node_index].append(node.costs[-1])
            tot_cost += node.costs[-1]
            tot_bandwidth += node.bandwidths[-1]
        for i, requester in enumerate(requesters):
            requester.record(unit_price)
            requester_data['bandwidths'][i].append(requester.bandwidths[-1])
            requester_data['costs'][i].append(-requester.costs[-1])
            tot_cost -= requester.costs[-1]
        total_cost_data.append(tot_cost)  # 记录总成本
        total_bandwidth_data.append(tot_bandwidth)  # 记录总带宽

    print("Request Num:", request_handler.request_num)
    print("Fetch Num:", request_handler.fetch_from_origin_num)
    print("Fetch Ratio:", request_handler.fetch_from_origin_num / request_handler.request_num * 100)

    # if not os.path.exists("./results"):
    #     os.mkdir("./results")
    # if not os.path.exists("./results/csv"):
    #     os.mkdir("./results/csv")
    #
    # for node in nodes:
    #     df = pd.DataFrame({'bandwidth': node.bandwidths, 'cost': node.costs})
    #     df.to_csv(f"./results/csv/node_{node.id}.csv", index=False)
    #
    # for requester in requesters:
    #     df = pd.DataFrame({'bandwidth': requester.bandwidths, 'cost': requester.costs})
    #     df.to_csv(f"./results/csv/{requester.app_id}.csv", index=False)

    if not os.path.exists("F:\\ECDN\\ECDN2.24\\ECDN\\results"):
        os.mkdir("F:\\ECDN\\ECDN2.24\\ECDN\\results")
    if not os.path.exists("F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv"):
        os.mkdir("F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv")

    for node in nodes:
        df = pd.DataFrame({'bandwidth': node.bandwidths, 'cost': node.costs})
        df.to_csv(f"F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv\\node_{node.id}.csv", index=False)

    for requester in requesters:
        df = pd.DataFrame({'bandwidth': requester.bandwidths, 'cost': requester.costs})
        df.to_csv(f"F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv\\{requester.app_id}.csv", index=False)

    # **新增：保存总成本数据**
    df_total_cost = pd.DataFrame({'total_cost': total_cost_data})
    df_total_cost.to_csv("F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv\\total_cost.csv", index=False)

    # **新增：保存总带宽数据**
    df_total_bandwidth = pd.DataFrame({'total_bandwidth': total_bandwidth_data})
    df_total_bandwidth.to_csv("F:\\ECDN\\ECDN2.24\\ECDN\\results\\csv\\total_bandwidth.csv", index=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    flask_thread.daemon = True
    flask_thread.start()
    main()
