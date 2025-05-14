import statistics

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator

import json
import tqdm

def run_simulation(setting, cost_method_combination, bandwidth_option_combination, ring_index=1):
    nodes = []
    bandwidth_sum = 0
    hostname_generator = Hostname_Generator()

    # 初始化节点
    for idx, node_type in enumerate(setting['nodes']):
        for i in range(node_type['num']):
            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=bandwidth_option_combination[idx],
                unit_price=node_type['unit_price'],
                cost_method=cost_method_combination[idx],
            ))
            bandwidth_sum += bandwidth_option_combination[idx]

    # 初始化哈希环和请求处理器
    hash_ring_1 = HashRing(nodes[0:300])  # 假设前300个节点为hash_ring_1
    request_handler_1 = RequestHandler(hash_ring_1)

    hash_ring_2 = HashRing(nodes[300:1500])  # 假设300-1500个节点为hash_ring_2
    request_handler_2 = RequestHandler(hash_ring_2)

    # 读取新增节点的 JSON 数据
    setting_add = json.load(open('add_nodes.json', 'r', encoding='utf-8'))
    new_nodes_data=[]
    for idx, node_type in enumerate(setting_add['nodes']):
        for i in range(node_type['num']):
            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=bandwidth_option_combination[idx],
                unit_price=node_type['unit_price'],
                cost_method=cost_method_combination[idx],
            ))
    # 如果ring_index是1，则添加节点到hash_ring_1，否则添加到hash_ring_2
    if ring_index == 1:
        for node_data in new_nodes_data:
            new_node = Node(
                hostname=hostname_generator.generate(),
                cache=node_data['cache'],
                bandwidth=node_data['bandwidth'],
                unit_price=node_data['unit_price'],
                cost_method=node_data['cost_method']
            )
            hash_ring_1.add_node(new_node)
            # print(f"Added new node {new_node.hostname} to hash_ring_1.")

    elif ring_index == 2:
        for node_data in new_nodes_data:
            new_node = Node(
                hostname=hostname_generator.generate(),
                cache=node_data['cache'],
                bandwidth=node_data['bandwidth'],
                unit_price=node_data['unit_price'],
                cost_method=node_data['cost_method']
            )
            hash_ring_2.add_node(new_node)
            # print(f"Added new node {new_node.hostname} to hash_ring_2.")

    # 初始化业务，将前3个business分配给hash_ring_1，其余4个分配给hash_ring_2
    businesses_ring_1 = []
    businesses_ring_2 = []
    for idx, business in enumerate(setting['businesses']):
        if idx < 3:
            businesses_ring_1.append(Business(
                app_id=business['app_id'],
                unit_price=business['unit_price'],
                cost_method=business['cost_method'],
                url_num=business['url_num'],
                wave_file=business['wave_file']
            ))
        else:
            businesses_ring_2.append(Business(
                app_id=business['app_id'],
                unit_price=business['unit_price'],
                cost_method=business['cost_method'],
                url_num=business['url_num'],
                wave_file=business['wave_file']
            ))

    tot_cost = 0
    for timestamp in tqdm.tqdm(range(0, 2592000, 300), desc="Processing timestamps"):
        # 处理hash_ring_1的业务
        for business in businesses_ring_1:
            business.send_request(request_handler_1, timestamp)

        # 处理hash_ring_2的业务
        for business in businesses_ring_2:
            business.send_request(request_handler_2, timestamp)

        # 记录节点的成本
        for node in nodes:
            node.record()
            if node.cost_method == 'B' and timestamp % 86400 == 0:
                tot_cost += node.get_cost()

        # 记录业务的成本
        for business in businesses_ring_1:
            business.record()
            if business.cost_method == 'B' and timestamp % 86400 == 0:
                tot_cost -= business.get_cost()

        for business in businesses_ring_2:
            business.record()
            if business.cost_method == 'B' and timestamp % 86400 == 0:
                tot_cost -= business.get_cost()

    # 计算A类业务的成本
    for node in nodes:
        if node.cost_method == 'A':
            tot_cost += node.get_cost() * 30
    for business in businesses_ring_1:
        if business.cost_method == 'A':
            tot_cost -= business.get_cost() * 30
    for business in businesses_ring_2:
        if business.cost_method == 'A':
            tot_cost -= business.get_cost() * 30

    return tot_cost  # 返回总成本


def main():
    # 读取设置文件
    setting_enum = json.load(open('settings.json', 'r', encoding='utf-8'))
    add_setting_enum = json.load(open('add_nodes.json', 'r', encoding='utf-8'))

    # 获取节点和业务配置
    setting = {
        "nodes": setting_enum["nodes"],
        "businesses": setting_enum["businesses"]
    }

    # 打印原始节点配置
    print(f"\n[Original Nodes Configuration]:")
    for i, node in enumerate(setting["nodes"]):
        print(f"  Node {i + 1}: {node}")
    print("The total number of nodes is 1500, with the first 1/5 forming a HashRing 1 and the last 4/5 forming HashRing 2.")

    print(f"\n[Addtional Nodes Configuration]:")
    for i, node in enumerate(add_setting_enum["nodes"]):
        print(f"  Node {i + 1}: {node}")

        # 哈希环1的业务配置（前3个业务）
        print("\n--- HashRing 1 (First 3 Businesses) ---")
        for i in range(3):
            print(f"  Business {i + 1}: {setting['businesses'][i]['app_id']}")

        # 哈希环2的业务配置（后4个业务）
        print("\n--- HashRing 2 (Last 4 Businesses) ---")
        for i in range(3, 7):  # 后4个业务
            print(f"  Business {i + 1}: {setting['businesses'][i]['app_id']}")

    # 打印新增节点配置
    # 第一次：添加新节点到 hash_ring_1
    # 第一次：添加新节点到 hash_ring_1
    print("\n--- Adding new nodes to HashRing 1 ---")
    cost_1_list = []
    for _ in range(10):  # 运行10次模拟
        cost_1 = run_simulation(
            setting_enum,
            [node['cost_method'] for node in setting["nodes"]],
            [node['bandwidth'] for node in setting["nodes"]],
            ring_index=1  # 添加到哈希环1
        )
        cost_1_list.append(cost_1)

    # 计算 HashRing 1 的平均值和方差
    avg_cost_1 = round(statistics.mean(cost_1_list), 2)
    variance_cost_1 = round(statistics.variance(cost_1_list), 2)

    print(f"Total Cost (HashRing 1): Average = {avg_cost_1}, Variance = {variance_cost_1}")

    # 第二次：添加新节点到 hash_ring_2
    print("\n--- Adding new nodes to HashRing 2 ---")
    cost_2_list = []
    for _ in range(10):  # 运行10次模拟
        cost_2 = run_simulation(
            setting_enum,
            [node['cost_method'] for node in setting["nodes"]],
            [node['bandwidth'] for node in setting["nodes"]],
            ring_index=2  # 添加到哈希环2
        )
        cost_2_list.append(cost_2)

    # 计算 HashRing 2 的平均值和方差
    avg_cost_2 = round(statistics.mean(cost_2_list), 2)
    variance_cost_2 = round(statistics.variance(cost_2_list), 2)

    print(f"Total Cost (HashRing 2): Average = {avg_cost_2}, Variance = {variance_cost_2}")

    # 计算两者的差异
    cost_diff = round(avg_cost_1 - avg_cost_2, 2)

    # 输出比较结果
    print(f"\n--- Comparison between HashRing 1 and HashRing 2 ---")
    print(f"Average Cost Difference: {cost_diff}")
    print(f"HashRing 1 Average Cost: {avg_cost_1}, HashRing 2 Average Cost: {avg_cost_2}")
    print(f"HashRing 1 Variance: {variance_cost_1}, HashRing 2 Variance: {variance_cost_2}")

if __name__ == "__main__":
    main()
