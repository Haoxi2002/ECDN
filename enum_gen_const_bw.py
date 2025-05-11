import json

# 原始数据中的 businesses
original_data = {
    "businesses": [
        {
            "app_id": "baidu",
            "unit_price": 1.0,
            "cost_method": "B",
            "url_num": 1000,
            "wave_file": "202503/business_baidu.csv"
        },
        {
            "app_id": "bytedance-iaas",
            "unit_price": 1.0,
            "cost_method": "A",
            "url_num": 1000,
            "wave_file": "202503/business_bytedance-iaas.csv"
        },
        {
            "app_id": "huya302-flv",
            "unit_price": 1.0,
            "cost_method": "A",
            "url_num": 1000,
            "wave_file": "202503/business_huya302-flv.csv"
        },
        {
            "app_id": "kwai-single",
            "unit_price": 1.0,
            "cost_method": "A",
            "url_num": 1000,
            "wave_file": "202503/business_kwai-single.csv"
        },
        {
            "app_id": "xhs",
            "unit_price": 1.0,
            "cost_method": "B",
            "url_num": 1000,
            "wave_file": "202503/business_xhs.csv"
        },
        {
            "app_id": "zijie-vod",
            "unit_price": 1.0,
            "cost_method": "A",
            "url_num": 1000,
            "wave_file": "202503/business_zijie-vod.csv"
        },
        {
            "app_id": "zijie302",
            "unit_price": 1.0,
            "cost_method": "A",
            "url_num": 1000,
            "wave_file": "202503/business_zijie302.csv"
        }
    ]
}

# 最大带宽限制
max_bandwidth = 512000

# 组合枚举：1024 带宽的节点数从 100 到 200，步长为 10
combinations = []

for num_1024 in range(100, 111, 10):
    total_bandwidth = num_1024 * 1024
    remaining_bandwidth = max_bandwidth - total_bandwidth
    if remaining_bandwidth >= 0:
        num_2048 = remaining_bandwidth // 2048
        combinations.append((num_1024, num_2048))

# 创建节点组合（每组只有两个节点对象）
node_groups = []
for i, (num_1024, num_2048) in enumerate(combinations):
    group = {
        "group_name": f"group{i + 1}",
        "nodes": [
            {
                "num": num_1024,
                "cache": 5000,
                "bandwidth": 1024,
                "unit_price": 1.0,
                "cost_method": "A"
            },
            {
                "num": num_2048,
                "cache": 5000,
                "bandwidth": 2048,
                "unit_price": 1.0,
                "cost_method": "B"
            }
        ]
    }
    node_groups.append(group)

# 构造最终输出
output = {
    "node_groups": node_groups,
    "businesses": original_data["businesses"]
}

# 写入 JSON 文件
with open("settings_enum_const_bw_test.json", "w") as f:
    json.dump(output, f, indent=2)

print("settings_enum_const_bw_test.json 已生成，每组包含两个节点配置")
