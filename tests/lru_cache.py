from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.keys = OrderedDict()

    def get(self, key: str) -> int:
        value = self.keys.get(key, -1)
        if value != -1:
            self.keys.move_to_end(key)
        return value

    def set(self, key: str, value: int) -> None:
        self.get(key)
        self.keys[key] = value

        if len(self.keys) > self.capacity:
            self.keys.popitem(last=False)
