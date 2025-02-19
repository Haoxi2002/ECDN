import random
import string

import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max


def cal_cost(bandwidth: list, cost_method: str):
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


class Hostname_Generator:
    def __init__(self):
        self.l = []

    def generate(self):
        new_hostname = f"bkj-{''.join(random.choices(string.hexdigits, k=8)).upper()}"
        while new_hostname in self.l:
            new_hostname = f"bkj-{''.join(random.choices(string.hexdigits, k=8)).upper()}"
        return new_hostname


class URL_Generator:
    def __init__(self, app_id, url_num):
        self.app_id = app_id
        self.url_num = url_num
        self.l = []
        self.generate()

    def generate(self):
        seen_urls = set(self.l)  # 使用集合加快查重速度
        while len(self.l) < self.url_num:
            new_url = f"http://{self.app_id}.com/{''.join(random.choices(string.ascii_letters + string.digits + '_', k=30)).lower()}"
            if new_url not in seen_urls:
                seen_urls.add(new_url)
                self.l.append(new_url)

    def get_url(self):
        return self.l[random.randint(0, len(self.l) - 1)]
