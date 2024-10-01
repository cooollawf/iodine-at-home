import heapq

class WRRScheduler:
    def __init__(self):
        self.servers = {}
        self.queue = []

    def add_server(self, server, weight):
        # 添加服务器及其权重到字典
        self.servers[server] = weight
        # 向队列中添加多个条目，数量由权重决定
        for _ in range(weight):
            heapq.heappush(self.queue, (-weight, server))

    def remove_server(self, server):
        # 移除所有与指定服务器相关的条目
        self.queue = [item for item in self.queue if item[1] != server]
        # 从字典中删除服务器
        del self.servers[server]

    def update_weight(self, server, new_weight):
        # 移除所有与指定服务器相关的条目
        self.queue = [item for item in self.queue if item[1] != server]
        # 更新字典中的权重
        self.servers[server] = new_weight
        # 添加新的条目
        for _ in range(new_weight):
            heapq.heappush(self.queue, (-new_weight, server))

    def next_server(self):
        if not self.queue:
            raise Exception("No available servers.")
        # 弹出队列中的第一个元素
        weight, server = heapq.heappop(self.queue)
        # 将权重减一后重新插入队列
        heapq.heappush(self.queue, (weight + 1, server))
        return server

# 示例用法
scheduler = WRRScheduler()

# 添加初始服务器及其权重
scheduler.add_server('server1', 0)
scheduler.add_server('server2', 0)
scheduler.add_server('server3', 0)

# 输出调度结果
for _ in range(10):
    print(scheduler.next_server())

# 更新权重
scheduler.update_weight('server1', 1)

# 继续输出更新权重后的调度结果
for _ in range(10):
    print(scheduler.next_server())

# 添加新服务器
scheduler.add_server('server4', 2)

# 继续输出调度结果
for _ in range(10):
    print(scheduler.next_server())

# 删除服务器
scheduler.remove_server('server2')

# 继续输出调度结果
for _ in range(10):
    print(scheduler.next_server())