import json
import tqdm

from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator


def main():
    setting = json.load(open('settings.json', 'r', encoding='utf-8'))

    # 初始化节点
    nodes = []
    bandwidth_sum = 0
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
            bandwidth_sum += node_type['bandwidth']

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

    tot_cost = 0
    # 业务发送请求
    for timestamp in tqdm.tqdm(range(0, 2592000, 300), desc="Processing timestamps"):
        for business in businesses:
            business.send_request(request_handler, timestamp)
        for node in nodes:
            node.record()
            if node.cost_method == 'B' and timestamp % 86400 == 0:
                tot_cost += node.get_cost()
        for business in businesses:
            business.record()
            if business.cost_method == 'B' and timestamp % 86400 == 0:
                tot_cost -= business.get_cost()

    for node in nodes:
        if node.cost_method == 'A':
            tot_cost += node.get_cost() * 30
    for business in businesses:
        if business.cost_method == 'A':
            tot_cost -= business.get_cost() * 30

    print('Total Cost: ' + str(tot_cost))


if __name__ == "__main__":
    main()
