import json
import tqdm
import statistics
from node import Node
from hash_ring import HashRing
from request_handler import RequestHandler
from business import Business
from util.tool import Hostname_Generator
from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def run_simulation(setting, cost_method_combination, bandwidth_option_combination):
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
    hash_ring = HashRing(nodes)
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

    tot_profit = 0
    for timestamp in tqdm.tqdm(range(0, 2592000, 300), desc="Processing timestamps"):
        for business in businesses:
            business.send_request(request_handler, timestamp)

        for node in nodes:
            node.record()
            if node.cost_method == 'B' and timestamp % 86400 == 0:
                tot_profit -= node.get_cost()

        for business in businesses:
            business.record()
            if business.cost_method == 'B' and timestamp % 86400 == 0:
                tot_profit += business.get_cost()

    for node in nodes:
        if node.cost_method == 'A':
            tot_profit -= node.get_cost() * 30
    for business in businesses:
        if business.cost_method == 'A':
            tot_profit += business.get_cost() * 30

    return tot_profit


def main():
    setting_enum = json.load(open('settings_enum_const_bw_test.json', 'r', encoding='utf-8'))
    all_results = []

    for group in setting_enum["node_groups"]:
        setting = {
            "nodes": group["nodes"],
            "businesses": setting_enum["businesses"]
        }

        group_name = group["group_name"]
        nodes = group["nodes"]

        last_total_profits = []

        # 打印当前 group 的详细配置
        print(f"\n[Group: {group_name}] 当前节点配置:")
        for i, node in enumerate(nodes):
            print(f"  Node {i + 1}: {node}")

        for _ in range(2):
            profit = run_simulation(
                setting,
                [node['cost_method'] for node in nodes],
                [node['bandwidth'] for node in nodes]
            )
            last_total_profits.append(profit)

        avg_profit = round(statistics.mean(last_total_profits), 2)  # 保留两位小数
        variance_profit = round(statistics.variance(last_total_profits), 2)  # 保留两位小数

        all_results.append({
            "group_name": group_name,
            "nodes": nodes,
            "config": {
                "nodes": nodes
            },
            "avg_profit": avg_profit,
            "variance_profit": variance_profit,
        })

        print(f"Group {group_name}:")
        print(f"  Average Profit: {avg_profit}")
        print(f"  Variance Profit: {variance_profit}")
        print("\n")

    # 配置展示
    print("\n--- Group Configurations ---")
    for result in all_results:
        print(f"\nGroup {result['group_name']} config:")
        for i, node in enumerate(result["config"]["nodes"]):
            print(f"  Node {i + 1}: {node}")

    # 表格展示
    print("\n--- Final Simulation Results ---")
    headers = ["Group", "Avg Profit", "Profit Var", "Avg Profit Diff"]

    # 设置基准组
    baseline_group_name = "group1"
    baseline = next((r for r in all_results if r['group_name'] == baseline_group_name), None)
    baseline_index = next(i for i, r in enumerate(all_results) if r['group_name'] == baseline_group_name)

    if baseline is None:
        raise ValueError(f"Baseline group '{baseline_group_name}' not found!")

    baseline_profit = baseline['avg_profit']

    # 构建数据，计算与 baseline 的差，保留两位小数
    table_data = [
        [
            r['group_name'],
            f"{r['avg_profit']:.2f}",  # 保留两位小数
            f"{r['variance_profit']:.2f}",  # 保留两位小数
            f"{r['avg_profit'] - baseline_profit:.2f}"  # 保留两位小数
        ]
        for r in all_results
    ]

    # 获取最大和最小利润
    max_profit_group = max(all_results, key=lambda x: x['avg_profit'])
    min_profit_group = min(all_results, key=lambda x: x['avg_profit'])

    # 计算最大和最小成本的差异
    max_min_text = f"Max Profit Group: {max_profit_group['group_name']} (Avg Profit: {max_profit_group['avg_profit']:.2f})\n"
    max_min_text += f"Min Profit Group: {min_profit_group['group_name']} (Avg Profit: {min_profit_group['avg_profit']:.2f})"

    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"Baseline Group: {baseline_group_name}")
    print(max_min_text)  # 打印最大最小成本的信息

    # 使用 PdfPages 生成 PDF
    with PdfPages("simulation_results.pdf") as pdf:
        # 第1页：表格 + 标题 + 最大最小成本注释 + 基准组标注
        df = pd.DataFrame(table_data, columns=headers)
        fig, ax = plt.subplots(figsize=(8.5, 0.6 * len(df) + 2))  # 留空间给标题
        ax.axis('off')
        ax.text(0.5, 1.05, "Enumeration Simulation Results", fontsize=14, ha='center', va='bottom', weight='bold')
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        ax.text(0, 0.05, max_min_text, ha='left', va='bottom', fontsize=10, weight='normal')  # 左对齐
        ax.text(0, -0.05, f"Baseline Group: {baseline_group_name}", ha='left', va='top', fontsize=10,
                weight='normal')  # 左对齐
        pdf.savefig(fig)
        plt.close()

        # 第2页：所有配置
        config_lines = []
        for result in all_results:
            config_lines.append(f"Group {result['group_name']} config:")
            for i, node in enumerate(result["config"]["nodes"]):
                config_lines.append(f"  Node {i + 1}: {node}")
            config_lines.append("")  # 每组之间空行
        config_text = "\n".join(config_lines)

        config_fig_height = 0.2 * len(config_lines) + 2
        fig, ax = plt.subplots(figsize=(8.5, config_fig_height))
        ax.axis('off')
        ax.text(0.5, 1.02, "Group Configurations", ha='center', va='top', fontsize=13, weight='bold')
        ax.text(0, 0.95, "\n" + config_text, va='top', ha='left', wrap=True, fontsize=10, family='monospace')
        pdf.savefig(fig)
        plt.close()

    print("Multi-page PDF saved to simulation.pdf")


if __name__ == "__main__":
    main()
