import json

from matplotlib import pyplot as plt

from util.entity import Request


class Requester:  # 业务
    def __init__(self, id: int, app_id: str, cost_method: str):
        self.id = id
        self.app_id = app_id
        self.cost_method = cost_method
        self.bw_list = {}  # 带宽列表，键为时间戳，值为该时间戳的带宽大小

    def send_request(self, request_handler):
        """随机选择路径发送请求"""
        request_datas = open("./data/202501200000_000_0", "r", encoding="utf-8").readlines()
        for line in request_datas:
            try:
                data = json.loads(line)
                request = Request(data['req_url'], data['ts'])
                response = request_handler.handle_request(request)
                if request.timestamp not in self.bw_list:
                    self.bw_list[request.timestamp] = 0
                self.bw_list[request.timestamp] += response.content_size
            except KeyError:
                # print("This request hasn't url or ts or ...")
                pass

    def draw_bw_list(self):
        bw_example = sorted(list(self.bw_list.items()), key=lambda t: t[0])
        x = range(len(bw_example))
        y = [value for _, value in bw_example]

        plt.plot(x, y)
        plt.xlabel('timestep')
        plt.ylabel('bandwidth')
        plt.title(f'app_{self.id}')
        plt.savefig(f'./img/app_{self.id}.png')
        plt.close()
