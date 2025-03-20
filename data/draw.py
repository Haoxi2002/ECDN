import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use('TkAgg')
df = pd.read_csv('wave1.csv')
data = df['log_count']
sampled_data = list(data[::300])

plt.figure(figsize=(10, 6))
plt.plot(sampled_data)

# 找出最大值和最小值及其索引
max_value = max(sampled_data)
min_value = min(sampled_data)
max_index = sampled_data.index(max_value)
min_index = sampled_data.index(min_value)

# 在图上标注最大值和最小值
plt.annotate(f'Max: {max_value:.0f}',
             xy=(max_index, max_value),
             xytext=(10, 10),
             textcoords='offset points',
             ha='left',
             va='bottom',
             bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

plt.annotate(f'Min: {min_value:.0f}',
             xy=(min_index, min_value),
             xytext=(10, -10),
             textcoords='offset points',
             ha='left',
             va='top',
             bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

plt.grid(True)
plt.title('Log Count / Day')
plt.xlabel('Timestamp (5min)')
plt.ylabel('Log Count')

plt.show()
plt.close()
