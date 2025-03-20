import datetime

import json
import os.path
import threading

import tqdm

import pandas as pd
from flask import Flask, render_template, jsonify

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator

app = Flask(__name__)
global_data = {
    "nodes": {},
    "businesses": {},
    "total_cost": [],
    "total_bandwidth": [],
    "timestamps": []
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def get_data():
    # 只返回最近8640个数据点（一个月）
    data_length = len(global_data["total_bandwidth"])
    start_idx = max(0, data_length - 8640)
    return jsonify({
        'nodes': {hostname: {
            "bandwidths": data["bandwidths"][start_idx:],
            "costs": data["costs"][start_idx:]
        } for hostname, data in global_data["nodes"].items()},
        'businesses': {app_id: {
            "bandwidths": data["bandwidths"][start_idx:],
            "costs": data["costs"][start_idx:]
        } for app_id, data in global_data["businesses"].items()},
        'total_cost': global_data["total_cost"][start_idx:],  # 添加总成本数据
        'total_bandwidth': global_data["total_bandwidth"][start_idx:],  # 添加总带宽数据
        'start_timestamp': start_idx * 300,
        'timestamps': list(range(start_idx * 300, start_idx * 300 + 8640 * 300, 300))
    })


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

    # 业务发送请求
    for timestamp in tqdm.tqdm(range(0, 2592000 * 2, 300), desc="Processing timestamps"):
        if timestamp == 5 * 86400:
            new_nodes = json.load(open('add_nodes.json', 'r', encoding='utf-8'))
            for node_type in new_nodes['nodes']:
                for i in range(node_type['num']):
                    new_node = Node(
                        hostname=hostname_generator.generate(),
                        cache=node_type['cache'],
                        bandwidth=node_type['bandwidth'],
                        unit_price=node_type['unit_price'],
                        cost_method=node_type['cost_method'],
                    )
                    new_node.bandwidths = [0] * (timestamp // 300)
                    new_node.costs = [0] * (timestamp // 300)
                    nodes.append(new_node)
                    hash_ring.add_node(new_node)
                    global_data["nodes"].setdefault(new_node.hostname, {"bandwidths": [0] * (timestamp // 300), "costs": [0] * (timestamp // 300)})
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
        global_data["total_cost"].append(tot_cost)
        global_data["total_bandwidth"].append(tot_bandwidth)
        global_data["timestamps"].append(timestamp)
        for node in nodes:
            global_data["nodes"].setdefault(node.hostname, {"bandwidths": [], "costs": []})
            global_data["nodes"][node.hostname]["bandwidths"].append(node.bandwidths[-1])
            global_data["nodes"][node.hostname]["costs"].append(node.costs[-1])
        for business in businesses:
            global_data["businesses"].setdefault(business.app_id, {"bandwidths": [], "costs": []})
            global_data["businesses"][business.app_id]["bandwidths"].append(business.bandwidths[-1])
            global_data["businesses"][business.app_id]["costs"].append(-1 * business.costs[-1])

    # 输出并保存结果
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

    df = pd.DataFrame({'bandwidth': global_data["total_bandwidth"], 'cost': global_data["total_cost"]})
    df.to_csv(f"./results/{save_time}/total.csv", index=False)


if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000}).start()
    main()
