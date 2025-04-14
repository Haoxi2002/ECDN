import json
import tqdm
import statistics
from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator
from tabulate import tabulate


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
    businesses = []
    bandwidth_sum = 0
    hostname_generator = Hostname_Generator()

    # 初始化节点，根据给定的cost_method_combination
    for idx, node_type in enumerate(setting['nodes']):
        for i in range(node_type['num']):
            cost_method = cost_method_combination[idx]
            nodes.append(Node(
                hostname=hostname_generator.generate(),
                cache=node_type['cache'],
                bandwidth=node_type['bandwidth'],
                unit_price=node_type['unit_price'],
                cost_method=cost_method,  # 使用对应的cost_method
            ))
            bandwidth_sum += node_type['bandwidth']

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

    # 使用两个数组分别封装 `node` 和 `business` 的总成本
    # node_method_costs[0] = node_method_cost_A, node_method_costs[1] = node_method_cost_B, node_method_costs[2-4] 保留给未来类型
    node_method_costs = [0] * 5
    # business_method_costs[0] = business_method_cost_A, business_method_costs[1] = business_method_cost_B, business_method_costs[2-4] 保留给未来类型
    business_method_costs = [0] * 5

    # 记录B类型节点和业务的每天最后一个cost
    daily_node_cost_B = 0  # 用于记录每天的节点cost
    daily_business_cost_B = 0  # 用于记录每天的业务cost

    # 统计一天的步骤数，每一天有288个步骤（5分钟一个步骤，一天24小时，一小时60分钟，一天共24*60/5=288个5分钟）
    step_per_day = 288
    step_counter = 0  # 计数器，用于跟踪当前是第几个步骤

    # 遍历时间戳，处理每个5分钟的时段
    for timestamp in tqdm.tqdm(range(0, 864000, 300), desc="Processing timestamps"):
        step_counter += 1  # 步骤加1

        # 处理每个业务的请求
        for business in businesses:
            business.send_request(request_handler, timestamp)

        tot_cost = 0
        tot_bandwidth = 0

        # 记录当天的最后一个节点cost
        for node in nodes:
            node.record()
            tot_cost += node.costs[-1]
            tot_bandwidth += node.bandwidths[-1]

            if node.cost_method == 'B':
                # B类型节点，每天记录最后一个值
                if step_counter == step_per_day:
                    daily_node_cost_B += node.costs[-1]  # 累加当天的节点cost（每天的最后一个值）

        # 记录当天的最后一个业务cost
        for business in businesses:
            business.record()
            tot_cost -= business.costs[-1]

            if business.cost_method == 'B':
                # B类型业务，每天记录最后一个值
                if step_counter == step_per_day:
                    daily_business_cost_B += business.costs[-1]  # 累加当天的业务cost（每天的最后一个值）

        # 将当前时刻的数据添加到全局数据
        global_data["total_cost"].append(tot_cost)
        global_data["total_bandwidth"].append(tot_bandwidth)
        global_data["timestamps"].append(timestamp)

        # 将节点的成本和带宽信息加入到全局数据
        for node in nodes:
            global_data["nodes"].setdefault(node.hostname, {"bandwidths": [], "costs": []})
            global_data["nodes"][node.hostname]["bandwidths"].append(node.bandwidths[-1])
            global_data["nodes"][node.hostname]["costs"].append(node.costs[-1])

        # 将业务的成本和带宽信息加入到全局数据
        for business in businesses:
            global_data["businesses"].setdefault(business.app_id, {"bandwidths": [], "costs": []})
            global_data["businesses"][business.app_id]["bandwidths"].append(business.bandwidths[-1])
            global_data["businesses"][business.app_id]["costs"].append(-1 * business.costs[-1])

        # 计算获取比率和带宽比率
        global_data["fetch_ratio"] = request_handler.fetch_from_origin_num / request_handler.request_num * 100
        global_data["bandwidth_ratio"] = tot_bandwidth / bandwidth_sum * 100

        # 每当完成一天（288步），将该天的总cost累加到总成本中
        if step_counter == step_per_day:
            # 对于B类型节点，每天的最后一个cost累加到总成本中
            node_method_costs[1] += daily_node_cost_B  # 累加B类型节点的总成本
            business_method_costs[1] += daily_business_cost_B  # 累加B类型业务的总成本

            # 重置每日的cost，以便下一天的累加
            daily_node_cost_B = 0
            daily_business_cost_B = 0

            # 重置步骤计数器
            step_counter = 0

    # 处理A类型的节点和业务，总成本为最后一个时间戳的cost乘以30（一个月）
    for node in nodes:
        if node.cost_method == 'A':
            node_method_costs[0] += node.costs[-1] * 30  # A类型节点，最后一个cost * 30（一个月）
        elif node.cost_method == 'B':
            # B类型节点已经在每天的最后一个cost中计算过了
            pass

    for business in businesses:
        if business.cost_method == 'A':
            business_method_costs[0] += business.costs[-1] * 30  # A类型业务，最后一个cost * 30（一个月）
        elif business.cost_method == 'B':
            # B类型业务已经在每天的最后一个cost中计算过了
            pass

    # 使用循环来计算business与node的总成本差异
    final_cost_difference = 0
    for i in range(5):  # 目前只考虑前两个类型
        final_cost_difference += -(business_method_costs[i] - node_method_costs[i])

    return final_cost_difference


# def run_simulation(setting, cost_method_combination):
#     nodes = []
#     bandwidth_sum = 0
#     hostname_generator = Hostname_Generator()
#
#     # Initialize nodes with given cost_method_combination
#     for idx, node_type in enumerate(setting['nodes']):
#         for i in range(node_type['num']):
#             cost_method = cost_method_combination[idx]
#             nodes.append(Node(
#                 hostname=hostname_generator.generate(),
#                 cache=node_type['cache'],
#                 bandwidth=node_type['bandwidth'],
#                 unit_price=node_type['unit_price'],
#                 cost_method=cost_method,  # Use cost_method from combination
#             ))
#             bandwidth_sum += node_type['bandwidth']
#
#     # Initialize hash ring and request handler
#     hash_ring = HashRing(nodes)
#     request_handler = RequestHandler(hash_ring)
#
#     # Initialize businesses
#     businesses = []
#     for business in setting['businesses']:
#         businesses.append(Business(
#             app_id=business['app_id'],
#             unit_price=business['unit_price'],
#             cost_method=business['cost_method'],
#             url_num=business['url_num'],
#             wave_file=business['wave_file']
#         ))
#
#     # Process timestamps
#     # 3 days
#     for timestamp in tqdm.tqdm(range(0, 259200, 300), desc="Processing timestamps"):
#         for business in businesses:
#             business.send_request(request_handler, timestamp)
#
#         tot_cost = 0
#         tot_bandwidth = 0
#         for node in nodes:
#             node.record()
#             tot_cost += node.costs[-1]
#             tot_bandwidth += node.bandwidths[-1]
#         for business in businesses:
#             business.record()
#             tot_cost -= business.costs[-1]
#
#         global_data["total_cost"].append(tot_cost)
#         global_data["total_bandwidth"].append(tot_bandwidth)
#         global_data["timestamps"].append(timestamp)
#
#         for node in nodes:
#             global_data["nodes"].setdefault(node.hostname, {"bandwidths": [], "costs": []})
#             global_data["nodes"][node.hostname]["bandwidths"].append(node.bandwidths[-1])
#             global_data["nodes"][node.hostname]["costs"].append(node.costs[-1])
#
#         for business in businesses:
#             global_data["businesses"].setdefault(business.app_id, {"bandwidths": [], "costs": []})
#             global_data["businesses"][business.app_id]["bandwidths"].append(business.bandwidths[-1])
#             global_data["businesses"][business.app_id]["costs"].append(-1 * business.costs[-1])
#
#         global_data["fetch_ratio"] = request_handler.fetch_from_origin_num / request_handler.request_num * 100
#         global_data["bandwidth_ratio"] = tot_bandwidth / bandwidth_sum * 100
#
#     return global_data["total_cost"][-1]  # Return the last total cost


def main():
    setting = json.load(open('settings.json', 'r', encoding='utf-8'))

    # Define all possible cost_method combinations (A and B)
    cost_method_options = ['A', 'B']
    node_count = len(setting['nodes'])

    # Generate all combinations of cost_methods
    from itertools import product
    cost_method_combinations = product(cost_method_options, repeat=node_count)

    # Store the results for each combination
    all_results = []

    # For each combination, run the simulation 10 times and store the result
    for combination in cost_method_combinations:
        last_total_costs = []
        for _ in range(10):  # Run the simulation 10 times for each combination
            global_data["total_cost"].clear()  # Clear the previous results
            last_total_cost = run_simulation(setting, combination)
            last_total_costs.append(last_total_cost)

        # Calculate average and variance for the last total costs
        avg_cost = round(statistics.mean(last_total_costs), 2)
        variance_cost = round(statistics.variance(last_total_costs), 2)

        # Store the results
        all_results.append({
            "combination": combination,
            "avg_cost": avg_cost,
            "variance_cost": variance_cost
        })

        # Print intermediate results during the simulation
        print(f"Cost Method Combination: {combination}")
        print(f"  Average Total Cost: {avg_cost}")
        print(f"  Variance of Total Cost: {variance_cost}")
        print("\n")

    # Print the final results after all simulations
    print("\n--- Final Simulation Results ---")
    headers = ["Cost Method Combination", "Average Total Cost", "Variance of Total Cost"]
    table_data = []

    for result in all_results:
        table_data.append([result['combination'], result['avg_cost'], result['variance_cost']])

    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()
