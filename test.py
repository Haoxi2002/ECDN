

def calc_month_95(bandwidth):
    sorted_bandwidth = sorted(bandwidth, reverse=True)
    print(sorted_bandwidth)
    top_95_index = round(len(sorted_bandwidth) * (1 - 0.95))  # 取top95%的点
    print(top_95_index)
    return round(sorted_bandwidth[top_95_index], 2)


a = list(range(1, 101))

print(calc_month_95(a))
