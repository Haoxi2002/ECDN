import json
import tqdm
from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator

global_data = {
    "nodes": {},
    "businesses": {},
    "total_cost": [],
    "total_bandwidth": [],
    "timestamps": [],
    "fetch_ratio": 0.0,
    "bandwidth_ratio": 0.0
}


def run_simulation(setting, cost_method_combination):
    nodes = []
    bandwidth_sum = 0
    hostname_generator = Hostname_Generator()

    # Initialize nodes with given cost_method_combination
    for idx, node_type in enumerate(setting['nodes']):
        for i in range(node_type['num']):
            cost_method = cost_method_combination[idx]
            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=node_type['bandwidth'],
                unit_price=node_type['unit_price'],
                cost_method=cost_method,  # Use cost_method from combination
            ))
            bandwidth_sum += node_type['bandwidth']

    # Initialize hash ring and request handler
    hash_ring = HashRing(nodes)
    request_handler = RequestHandler(hash_ring)

    # Initialize businesses
    businesses = []
    for business in setting['businesses']:
        businesses.append(Business(
            app_id=business['app_id'],
            unit_price=business['unit_price'],
            cost_method=business['cost_method'],
            url_num=business['url_num'],
            wave_file=business['wave_file']
        ))

    # Process timestamps
    for timestamp in tqdm.tqdm(range(0, 2592000, 300), desc="Processing timestamps"):
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

        global_data["fetch_ratio"] = request_handler.fetch_from_origin_num / request_handler.request_num * 100
        global_data["bandwidth_ratio"] = tot_bandwidth / bandwidth_sum * 100

    return global_data["total_cost"][-1]  # Return the last total cost


def main():
    setting = json.load(open('settings.json', 'r', encoding='utf-8'))

    # Define all possible cost_method combinations (A and B)
    cost_method_options = ['A', 'B']
    node_count = len(setting['nodes'])

    # Generate all combinations of cost_methods
    from itertools import product
    cost_method_combinations = product(cost_method_options, repeat=node_count)

    # For each combination, run the simulation and print the result
    for combination in cost_method_combinations:
        global_data["total_cost"].clear()  # Clear the previous results
        print(f"Running simulation for cost_method combination: {combination}")
        last_total_cost = run_simulation(setting, combination)
        print(f"Last total_cost for combination {combination}: {last_total_cost}")


if __name__ == "__main__":
    main()
