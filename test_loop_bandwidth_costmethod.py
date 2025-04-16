from fpdf import FPDF
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
import os

global_data = {
    "nodes": {},
    "businesses": {},
    "total_cost": [],
    "total_bandwidth": [],
    "timestamps": [],
    "fetch_ratio": 0.0,
    "bandwidth_ratio": 0.0
}


def generate_pdf(results):
    # Create the results folder if it doesn't exist
    output_folder = './results'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create a PDF object
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Simulation Results", ln=True, align="C")

    # Line break
    pdf.ln(10)

    # Table headers with smaller font
    pdf.set_font("Arial", 'B', 10)  # Reduce the font size of the headers
    headers = ["Cost Method Combination", "Bandwidth Combination", "Average Total Cost", "Variance of Total Cost"]

    # Adjusted column width to fit the content
    column_width = 45
    for header in headers:
        pdf.cell(column_width, 10, header, border=1, align="C")
    pdf.ln()

    # Table content
    pdf.set_font("Arial", '', 10)  # Set a slightly smaller font for the content
    for result in results:
        pdf.cell(column_width, 10, str(result['cost_combination']), border=1, align="C")
        pdf.cell(column_width, 10, str(result['bandwidth_combination']), border=1, align="C")
        pdf.cell(column_width, 10, str(result['avg_cost']), border=1, align="C")
        pdf.cell(column_width, 10, str(result['variance_cost']), border=1, align="C")
        pdf.ln()

    # Line break before max/min values
    pdf.ln(10)

    # Max and Min Average Cost with line breaks to prevent overflow
    max_result = max(results, key=lambda x: x['avg_cost'])
    min_result = min(results, key=lambda x: x['avg_cost'])

    pdf.set_font("Arial", 'B', 10)
    # Add line breaks and fit text within the page
    pdf.cell(200, 10, txt=f"Maximum Average Total Cost: {max_result['avg_cost']}", ln=True)
    pdf.cell(200, 10,
             txt=f"(Cost Combination: {max_result['cost_combination']}, Bandwidth Combination: {max_result['bandwidth_combination']})",
             ln=True)
    pdf.ln(5)  # Small break between max and min
    pdf.cell(200, 10, txt=f"Minimum Average Total Cost: {min_result['avg_cost']}", ln=True)
    pdf.cell(200, 10,
             txt=f"(Cost Combination: {min_result['cost_combination']}, Bandwidth Combination: {min_result['bandwidth_combination']})",
             ln=True)

    # Save the PDF to the specified folder
    pdf.output(f"{output_folder}/simulation_results.pdf")


def run_simulation(setting, cost_method_combination, bandwidth_option_combination):
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

    # 使用两个数组分别封装 `node` 和 `business` 的总成本
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

    return final_cost_difference


def main():
    setting = json.load(open('settings.json', 'r', encoding='utf-8'))

    # Define all possible cost_method combinations (A and B)
    cost_method_options = ['A', 'B']
    node_count = len(setting['nodes'])

    # Generate all combinations of cost_methods (for 8 combinations)
    # 这将枚举8个组合，比如（A, A, A, A）、（A, A, A, B）等
    cost_method_combinations = list(product(cost_method_options, repeat=node_count))
    # print(f"Cost method combinations: {cost_method_combinations}")

    # 定义带宽选项（现在只有1024）
    bandwidth_options = [1024]

    # 生成所有可能的带宽配置组合，并将其转换为列表
    bandwidth_option_combinations = list(product(bandwidth_options, repeat=node_count))
    # print(f"Bandwidth combinations: {bandwidth_option_combinations}")

    all_results = []

    cost_method_combinations = [('A','A','A'),('A','B','A'),('A','B','B'),('B','B','B')]
    bandwidth_option_combinations = [(1024, 1024, 1024), (1024, 2048, 1024), (1024, 2048, 2048), (2048, 2048, 2048)]

    # cost_method_combinations = [('A', 'A', 'A')]
    # bandwidth_option_combinations = [(1024, 1024, 1024), (1024, 2048, 1024)]

    # 对于每个cost_method组合和每个bandwidth配置组合，运行2次模拟并存储结果
    for cost_combination in cost_method_combinations:
        # 重新生成带宽组合，确保每个cost_method组合都和所有带宽组合进行配对
        for bandwidth_combination in bandwidth_option_combinations:
            last_total_costs = []
            for _ in range(5):  # 对每个组合运行2次模拟
                global_data["total_cost"].clear()  # Clear the previous results
                last_total_cost = run_simulation(setting, cost_combination, bandwidth_combination)
                last_total_costs.append(last_total_cost)
            print(
                f"Last Total Costs for Cost Combination {cost_combination} and Bandwidth Combination {bandwidth_combination}: {last_total_costs}")

            # Calculate average and variance for the last total costs
            avg_cost = round(statistics.mean(last_total_costs), 2)
            variance_cost = round(statistics.variance(last_total_costs), 2)

            # Store the results
            all_results.append({
                "cost_combination": cost_combination,
                "bandwidth_combination": bandwidth_combination,
                "avg_cost": avg_cost,
                "variance_cost": variance_cost
            })



            # Print intermediate results during the simulation
            print(f"Cost Method Combination: {cost_combination}, Bandwidth Combination: {bandwidth_combination}")
            print(f"  Average Total Cost: {avg_cost}")
            print(f"  Variance of Total Cost: {variance_cost}")
            print("\n")

    # Generate PDF with results
    generate_pdf(all_results)

    # Print the final results after all simulations
    print("\n--- Final Simulation Results ---")
    headers = ["Cost Method Combination", "Bandwidth Combination", "Average Total Cost", "Variance of Total Cost"]
    table_data = []

    for result in all_results:
        table_data.append(
            [result['cost_combination'], result['bandwidth_combination'], result['avg_cost'], result['variance_cost']])

    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()