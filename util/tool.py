import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max

def cal_cost(bandwidth: list, cost_method: str):
    """
    计算带宽费用。

    :param bandwidth: 一个包含带宽数据的列表，每个元素表示每个5分钟的打点。
    :param cost_method: 计费模式的编码（如 'A'、'B'、'C'、'D'、'E'）。
    :return: 计算出的费用
    """
    # 计算月95
    def calc_month_95():
        # 先按降序排列带宽数据
        sorted_bandwidth = sorted(bandwidth, reverse=True)
        # 选择Top95%的点
        top_95_index = int(len(sorted_bandwidth) * 0.95)
        return sum(sorted_bandwidth[:top_95_index]) / len(sorted_bandwidth)

    # 计算日95
    def calc_day_95():
        # 假设每一天有288个5分钟数据点（24小时 * 60分钟 / 5分钟 = 288个点）
        daily_bandwidth = [sum(bandwidth[i:i + 288]) / 288 for i in range(0, len(bandwidth), 288)]
        daily_bandwidth.sort(reverse=True)
        day_95_index = int(len(daily_bandwidth) * 0.95)
        return sum(daily_bandwidth[:day_95_index]) / len(daily_bandwidth)

    # 计算晚高峰95
    def calc_peak_95():
        # 假设晚高峰时间为18:00-23:00，即从第108个点到第144个点
        peak_bandwidth = bandwidth[108:144]
        peak_bandwidth.sort(reverse=True)
        peak_95_index = int(len(peak_bandwidth) * 0.95)
        return sum(peak_bandwidth[:peak_95_index]) / len(peak_bandwidth)

    # 计算买断费用
    def calc_flat_rate():
        # 买断费按定值收取，可以是一个固定费用
        return 1000  # 常量

    # 计算日峰值月平均
    def calc_daily_peak_avg():
        # 获取每一天的最大带宽（即一天中的最大值，288个数据点为一天）
        daily_peaks = [max(bandwidth[i:i + 288]) for i in range(0, len(bandwidth), 288)]
        return sum(daily_peaks) / len(daily_peaks)

    # 根据计费模式选择对应的费用计算方法
    if cost_method == 'A':
        return calc_month_95()
    elif cost_method == 'B':
        return calc_day_95()
    elif cost_method == 'C':
        return calc_peak_95()
    elif cost_method == 'D':
        return calc_flat_rate()
    elif cost_method == 'E':
        return calc_daily_peak_avg()
    else:
        raise ValueError("Invalid cost method code")  # 如果计费方式无效，抛出异常