import random
import string

import numpy as np
import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max


def cal_cost(bandwidth: list, cost_method: str):
    remainder_month = len(bandwidth) % 8640
    if remainder_month == 0:
        # 如果余数是0，表示数据长度正好是 8640 的整数倍，取最后 8640 个元素
        bandwidth_month = bandwidth[-8640:]
    else:
        # 如果余数不为0，取最后余数个元素，补足一个月
        bandwidth_month = bandwidth[-remainder_month:]

    remainder_day = len(bandwidth_month) % 288
    if remainder_day == 0:
        # 如果余数是0，表示数据长度正好是 288 的整数倍，取最后一天的288个元素
        bandwidth_day = bandwidth_month[-288:]
    else:
        #  如果余数不为0，取最后余数个元素，补足一天
        bandwidth_day = bandwidth_month[-remainder_day:]

    def calc_month_95():  # 月95
        # 从小到大排序带宽数据
        sorted_bandwidth_month = np.sort(bandwidth_month)
        # 计算95%的索引，取最接近95%的点
        top_95_index = int(np.ceil(len(sorted_bandwidth_month) * 0.95)) - 1
        # 返回该位置的值，四舍五入保留两位小数
        return round(float(sorted_bandwidth_month[top_95_index]), 2)

    def calc_day_95():
        # 按照升序排序
        sorted_bandwidth_day = sorted(bandwidth_day)
        # 取95%位置的带宽
        day_95_index = round(len(sorted_bandwidth_day) * 0.95) - 1  # 取95%位置的点
        # 返回该位置的值，四舍五入保留两位小数
        return round(sorted_bandwidth_day[day_95_index], 2)

    def calc_day_peak_95():
        # 如果数据长度小于240，返回0（没有足够的晚高峰数据）
        if len(bandwidth_day) <= 240:
            return 0
        # 从240到288之间的数据，晚高峰确认后为晚上8点到12点
        peak_bandwidth_day = bandwidth_day[240:]
        # 对选取的数据进行升序排序
        peak_bandwidth_day.sort()
        # 计算95%位置的带宽值
        peak_95_index = round(len(peak_bandwidth_day) * 0.95) - 1
        return round(peak_bandwidth_day[peak_95_index], 2)

    def calc_flat_rate():  # 买断
        return round(1, 2)

    def calc_day_peak_month_avg():  # 日峰值月平均
        # 获取每日的最大值
        daily_peaks = []
        for i in range(0, len(bandwidth_month), 288):
            # 取当前段的最大值，如果剩余的不足288个元素，只取这些剩余部分
            daily_peaks.append(max(bandwidth_month[i:i + 288]))
        # 计算并返回月平均值
        return round(sum(daily_peaks) / len(daily_peaks), 2)

    strategies = {
        'A': calc_month_95,
        'B': calc_day_95,
        'C': calc_day_peak_95,
        'D': calc_flat_rate,
        'E': calc_day_peak_month_avg
    }
    if cost_method not in strategies:
        raise ValueError(...)
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
