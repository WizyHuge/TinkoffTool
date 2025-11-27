from abc import ABC, abstractmethod
from collections import deque


class BaseStrategy(ABC):
    def __init__(self, name):
        self.name = name
        self.price_history = deque(maxlen=1000)
        
    def add_price(self, price):
        self.price_history.appendleft(price)
        
    @abstractmethod
    def analyze(self, current_price):
        pass
        
    def get_indicator_values(self):
        return {}
        
    def reset(self):
        self.price_history.clear()


def calculate_ma(prices, period):
    if len(prices) < period:
        return None
    return sum(list(prices)[-period:]) / period


def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
        
    price_list = list(prices)
    gains = []
    losses = []
    
    for i in range(len(price_list) - period, len(price_list)):
        if i == 0:
            continue
        change = price_list[i] - price_list[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if not gains or sum(losses) == 0:
        return None
        
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_std(prices, period):
    if len(prices) < period:
        return None
        
    price_list = list(prices)[-period:]
    mean = sum(price_list) / period
    variance = sum((x - mean) ** 2 for x in price_list) / period
    return variance ** 0.5

