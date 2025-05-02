import random
import string

import numpy as np
import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max


def cal_cost(bandwidth: list, cost_method: str, unit_price: float):
    # 计算月数据（最后 8640 个点或补足）
    remainder_month = len(bandwidth) % 8640
    bandwidth_month = bandwidth[-remainder_month:] if remainder_month != 0 else bandwidth[-8640:]

    # 计算日数据（最后 288 个点或补足）
    remainder_day = len(bandwidth_month) % 288
    bandwidth_day = bandwidth_month[-remainder_day:] if remainder_day != 0 else bandwidth_month[-288:]

    def calc_month_95():
        # 使用 partition 快速找到 95% 分位数（无需全排序）
        k = int(len(bandwidth_month) * 0.95)
        # 用 partition 将前 k 小的数放在左边，第 k 个数即 95% 分位数
        partitioned = np.partition(bandwidth_month, k)
        return round(float(partitioned[k]), 2) * unit_price

    def calc_day_95():
        k = round(len(bandwidth_day) * 0.95) - 1
        partitioned = np.partition(bandwidth_day, k)
        return round(float(partitioned[k]), 2) * unit_price

    def calc_day_peak_95():
        if len(bandwidth_day) <= 240:
            return 0
        peak_bandwidth_day = bandwidth_day[240:]
        k = round(len(peak_bandwidth_day) * 0.95) - 1
        partitioned = np.partition(peak_bandwidth_day, k)
        return round(float(partitioned[k]), 2) * unit_price

    def calc_flat_rate():
        return round(1.0, 2) * unit_price

    def calc_day_peak_month_avg():
        daily_peaks = [
            np.max(bandwidth_month[i:i + 288])
            for i in range(0, len(bandwidth_month), 288)
        ]
        return round(np.mean(daily_peaks), 2) * unit_price

    strategies = {
        'A': calc_month_95,
        'B': calc_day_95,
        'C': calc_day_peak_95,
        'D': calc_flat_rate,
        'E': calc_day_peak_month_avg
    }
    if cost_method not in strategies:
        raise ValueError("Invalid cost_method")
    return strategies[cost_method]()


class Hostname_Generator:
    def __init__(self):
        self.generated = set()

    def generate(self):
        while True:
            new_hostname = f"bkj-{''.join(random.choices(string.hexdigits, k=8)).upper()}"
            if new_hostname not in self.generated:
                self.generated.add(new_hostname)
                return new_hostname


class URL_Generator:
    def __init__(self, app_id, url_num):
        self.app_id = app_id
        self.url_num = url_num
        self.modify_period = 172800 // self.url_num
        self.last_modify = 0
        self.l = []
        self.seen_urls = set(self.l)
        self.generate()

    def generate(self):
        while len(self.l) < self.url_num:
            new_url = f"http://{self.app_id}.com/{''.join(random.choices(string.ascii_letters + string.digits + '_', k=30)).lower()}"
            if new_url not in self.seen_urls:
                self.seen_urls.add(new_url)
                self.l.append(new_url)

    def get_url(self, timestamp):
        if timestamp - self.last_modify > self.modify_period:
            drop_index = random.randint(0, self.url_num - 1)
            new_url = f"http://{self.app_id}.com/{''.join(random.choices(string.ascii_letters + string.digits + '_', k=30)).lower()}"
            while new_url in self.seen_urls:
                new_url = f"http://{self.app_id}.com/{''.join(random.choices(string.ascii_letters + string.digits + '_', k=30)).lower()}"
            self.seen_urls.remove(self.l[drop_index])
            self.seen_urls.add(new_url)
            self.l[drop_index] = new_url
            self.last_modify = timestamp

        return self.l[random.randint(0, self.url_num - 1)]
