import math
import random
import string

import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max


def cal_cost(bandwidth: list, cost_method: str):
    def calc_month_95():
        sorted_bandwidth = sorted(bandwidth, reverse=True)
        top_95_index = int(len(sorted_bandwidth) * (1 - 0.95))# 取top95%的点
        return round(sorted_bandwidth[top_95_index], 2)

    def calc_day_95():
        daily_bandwidth_95 = []
        # 遍历每一天（假设一天有288个数据点）
        for i in range(0, len(bandwidth), 288):
            daily_data = bandwidth[i:i + 288]
            daily_data.sort(reverse=True)  # 每天的带宽排序
            day_95_index = int(len(daily_data) * (1 - 0.95))  # 取top95%的点
            daily_bandwidth_95.append(daily_data[day_95_index])  # 记录该点的带宽
        # 计算所有日95值的平均值
        return round(sum(daily_bandwidth_95) / len(daily_bandwidth_95), 2)

    def calc_peak_95():
        daily_peak_95 = []  # 存储每一天的95%带宽值
        # 遍历30天，每天的240到276晚高峰数据
        for i in range(0, len(bandwidth), 288):
            peak_bandwidth = bandwidth[i + 240:i + 276]  # 提取每天的240到276数据（晚上8点到晚上11点）
            peak_bandwidth.sort(reverse=True)  # 对该天数据进行降序排序
            peak_95_index = int(len(peak_bandwidth) * (1 - 0.95))  # 找到该天95%点的索引
            daily_peak_95.append(round(peak_bandwidth[peak_95_index], 2))  # 添加到日均列表
        # 计算所有天数的95%带宽值的平均值
        return round(sum(daily_peak_95) / len(daily_peak_95), 2)

    def calc_flat_rate():
        return round(150, 2)

    def calc_daily_peak_avg():
        daily_peaks = [max(bandwidth[i:i + 288]) for i in range(0, len(bandwidth), 288)]
        return round(sum(daily_peaks) / len(daily_peaks), 2)

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
        raise ValueError("Invalid cost method code")


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
