import json
import tqdm
import statistics
from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator
from tabulate import tabulate
from itertools import product

global_data = {
    "nodes": {},
    "businesses": {},
    "total_cost": [],
    "total_bandwidth": [],
    "timestamps": [],
    "fetch_ratio": 0.0,
    "bandwidth_ratio": 0.0
}


def run_simulation(setting, cost_method_combination, bandwidth_option_combination):
    global tot_bandwidth
    nodes = []
    businesses = []
    bandwidth_sum = 0
    hostname_generator = Hostname_Generator()
    # 初始化节点，根据给定的cost_method_combination和bandwidth_option_combination
    for idx, node_type in enumerate(setting['nodes']):
        for i in range(node_type['num']):
            cost_method = cost_method_combination[idx]
            bandwidth = bandwidth_option_combination[idx]  # 从bandwidth_option_combination中获取每个节点的带宽

            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=bandwidth,
                unit_price=node_type['unit_price'],
                cost_method=cost_method,  # 使用对应的cost_method
            ))
            bandwidth_sum += bandwidth

    hash_ring = HashRing(nodes)
    request_handler = RequestHandler(hash_ring)

    # 初始化业务
    for business in setting['businesses']:
        businesses.append(Business(
            app_id=business['app_id'],
            unit_price=business['unit_price'],
            cost_method=business['cost_method'],
            url_num=business['url_num'],
            wave_file=business['wave_file']
        ))

    # 使用两个数组分别封装 `node` 和 `business` 的总成本，5代表不同的计费方式，目前主要是A,B两种
    node_method_costs = [0] * 5
    business_method_costs = [0] * 5

    daily_node_cost_B = 0
    daily_business_cost_B = 0
    step_per_day = 288
    step_counter = 0

    for timestamp in tqdm.tqdm(range(0, 2592000, 300), desc="Processing timestamps"):
        step_counter += 1  # 步骤加1

        for business in businesses:
            business.send_request(request_handler, timestamp)

        tot_cost = 0
        tot_bandwidth = 0

        for node in nodes:
            node.record()
            tot_cost += node.costs[-1]
            tot_bandwidth += node.bandwidths[-1]

            if node.cost_method == 'B' and step_counter == step_per_day:
                daily_node_cost_B += node.costs[-1]

        for business in businesses:
            business.record()
            tot_cost -= business.costs[-1]

            if business.cost_method == 'B' and step_counter == step_per_day:
                daily_business_cost_B += business.costs[-1]

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

        if step_counter == step_per_day:
            node_method_costs[1] += daily_node_cost_B
            business_method_costs[1] += daily_business_cost_B
            daily_node_cost_B = 0
            daily_business_cost_B = 0
            step_counter = 0

    for node in nodes:
        if node.cost_method == 'A':
            node_method_costs[0] += node.costs[-1] * 30
        elif node.cost_method == 'B':
            pass

    for business in businesses:
        if business.cost_method == 'A':
            business_method_costs[0] += business.costs[-1] * 30
        elif business.cost_method == 'B':
            pass

    final_cost_difference = 0
    for i in range(5):
        final_cost_difference += -(business_method_costs[i] - node_method_costs[i])

    return tot_bandwidth, final_cost_difference



def main():
    setting_enum = json.load(open('settings_enum.json', 'r', encoding='utf-8'))

    all_results = []

    for group in setting_enum["node_groups"]:
        setting = {
            "nodes": group["nodes"],
            "businesses": setting_enum["businesses"]
        }

        group_name = group["group_name"]
        nodes = group["nodes"]

        last_total_costs = []
        last_bandwidths = []

        # 打印当前 group 的详细配置（每个节点）
        print(f"\n[Group: {group_name}] 当前节点配置:")
        for i, node in enumerate(nodes):
            print(f"  Node {i + 1}: {node}")

        for _ in range(10):
            global_data["total_cost"].clear()
            global_data["total_bandwidth"].clear()
            bandwidth, total_cost = run_simulation(
                setting,
                [node['cost_method'] for node in nodes],
                [node['bandwidth'] for node in nodes]
            )
            last_total_costs.append(total_cost)
            last_bandwidths.append(bandwidth)

        avg_cost = round(statistics.mean(last_total_costs), 2)
        variance_cost = round(statistics.variance(last_total_costs), 2)
        avg_bandwidth = round(statistics.mean(last_bandwidths), 2)
        variance_bandwidth = round(statistics.variance(last_bandwidths), 2)

        # 保存到结果中，包含完整节点配置
        all_results.append({
            "group_name": group_name,
            "nodes": nodes,
            "config": {
                "nodes": nodes  # 用 config 包一层，方便程序处理配置
            },
            "avg_cost": avg_cost,
            "variance_cost": variance_cost,
            "avg_bandwidth": avg_bandwidth,
            "variance_bandwidth": variance_bandwidth
        })

        print(f"Group {group_name}:")
        print(f"  Average Cost: {avg_cost}")
        print(f"  Variance Cost: {variance_cost}")
        print(f"  Average Bandwidth: {avg_bandwidth}")
        print(f"  Variance Bandwidth: {variance_bandwidth}")
        print("\n")

    # 配置展示
    print("\n--- Group Configurations ---")
    for result in all_results:
        print(f"\nGroup {result['group_name']} config:")
        for i, node in enumerate(result["config"]["nodes"]):
            print(f"  Node {i + 1}: {node}")

    # 表格展示
    print("\n--- Final Simulation Results ---")
    headers = ["Group", "Avg Cost", "Cost Var", "Avg Bandwidth", "BW Var"]
    table_data = [
        [r['group_name'], r['avg_cost'], r['variance_cost'], r['avg_bandwidth'], r['variance_bandwidth']]
        for r in all_results
    ]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # 保存 JSON 文件
    with open("test/simulation_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
        print("\nResults written to simulation_summary.json")



if __name__ == "__main__":
    main()