import json
import itertools
import copy

# 原始数据中的 businesses
original_data = {
    "businesses":[
    {
      "app_id":"baidu",
      "unit_price":1.0,
      "cost_method":"B",
      "url_num":1000,
      "wave_file":"202503/business_baidu.csv"
    },
    {
      "app_id":"bytedance-iaas",
      "unit_price":1.0,
      "cost_method":"A",
      "url_num":1000,
      "wave_file":"202503/business_bytedance-iaas.csv"
    },
    {
      "app_id":"huya302-flv",
      "unit_price":1.0,
      "cost_method":"A",
      "url_num":1000,
      "wave_file":"202503/business_huya302-flv.csv"
    },
    {
      "app_id":"kwai-single",
      "unit_price":1.0,
      "cost_method":"A",
      "url_num":1000,
      "wave_file":"202503/business_kwai-single.csv"
    },
    {
      "app_id":"xhs",
      "unit_price":1.0,
      "cost_method":"B",
      "url_num":1000,
      "wave_file":"202503/business_xhs.csv"
    },
    {
      "app_id":"zijie-vod",
      "unit_price":1.0,
      "cost_method":"A",
      "url_num":1000,
      "wave_file":"202503/business_zijie-vod.csv"
    },
    {
      "app_id":"zijie302",
      "unit_price":1.0,
      "cost_method":"A",
      "url_num":1000,
      "wave_file":"202503/business_zijie302.csv"
    }
  ]
}

# 两种配置
config_options = [
    {"cost_method": "A", "bandwidth": 1024, "unit_price": 1.0},
    {"cost_method": "A", "bandwidth": 2048, "unit_price": 1.0},
    {"cost_method": "B", "bandwidth": 2048, "unit_price": 1.02}
]

# 假设每组有 3 个节点，枚举所有组合
node_combinations = list(itertools.product(config_options, repeat=3))

node_groups = []
for i, combo in enumerate(node_combinations):
    group = {
        "group_name": f"group{i+1}",
        "nodes": []
    }
    for config in combo:
        node = {
            "num": 500,
            "cache": 5000,
            "bandwidth": config["bandwidth"],
            "unit_price": config["unit_price"],
            "cost_method": config["cost_method"]
        }
        group["nodes"].append(node)
    node_groups.append(group)

# 构造最终结果
output = {
    "node_groups": node_groups,
    "businesses": original_data["businesses"]
}

# 写入 JSON 文件
with open("settings_enum.json", "w") as f:
    json.dump(output, f, indent=2)

print("settings_enum.json 已生成，包含所有节点组合")
