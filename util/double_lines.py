import pandas as pd
import matplotlib.pyplot as plt

# 设置全局样式，确保背景为白色
plt.style.use('default')

# 文件路径
bandwidth_file1 = r'F:\ECDN\ECDN2.24\ECDN\results\csv\total_bandwidth.csv'
bandwidth_file2 = r'F:\ECDN\ECDN2.24\ECDN\results\csv2\total_bandwidth.csv'
cost_file1 = r'F:\ECDN\ECDN2.24\ECDN\results\csv\total_cost.csv'
cost_file2 = r'F:\ECDN\ECDN2.24\ECDN\results\csv2\total_cost.csv'

# 读取数据（确保不把第一行当作数据）
df_bandwidth1 = pd.read_csv(bandwidth_file1, names=["total_bandwidth"], skiprows=1)
df_bandwidth2 = pd.read_csv(bandwidth_file2, names=["total_bandwidth"], skiprows=1)
df_cost1 = pd.read_csv(cost_file1, names=["total_cost"], skiprows=1)
df_cost2 = pd.read_csv(cost_file2, names=["total_cost"], skiprows=1)

# 仅取前 1000 个数据点
df_bandwidth1 = df_bandwidth1[:1000]
df_bandwidth2 = df_bandwidth2[:1000]
df_cost1 = df_cost1[:1000]
df_cost2 = df_cost2[:1000]

# 创建索引作为横轴
x_bandwidth = range(len(df_bandwidth1))
x_cost = range(len(df_cost1))

# 绘制带宽曲线
plt.figure(figsize=(10, 5), facecolor='white')  # 确保背景为白色
plt.plot(x_bandwidth, df_bandwidth1["total_bandwidth"], label="Bandwidth 1", linestyle='-')
plt.plot(x_bandwidth, df_bandwidth2["total_bandwidth"], label="Bandwidth 2", linestyle='--')
plt.xlabel("Index")
plt.ylabel("Total Bandwidth")
plt.title("Bandwidth Comparison (First 1000 Points)")
plt.legend()
plt.grid()
plt.show()

# 绘制成本曲线
plt.figure(figsize=(10, 5), facecolor='white')  # 确保背景为白色
plt.plot(x_cost, df_cost1["total_cost"], label="Cost 1", linestyle='-')
plt.plot(x_cost, df_cost2["total_cost"], label="Cost 2", linestyle='--')
plt.xlabel("Index")
plt.ylabel("Total Cost")
plt.title("Cost Comparison (First 1000 Points)")
plt.legend()
plt.grid()
plt.show()
