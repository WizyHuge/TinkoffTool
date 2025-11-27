class SimpleFastStrategy:
    def __init__(self):
        self.last_price = None
        self.price_history = []
        self.threshold = 0.001  

    def add_price(self, price: float):
        self.price_history.append(price)

        if len(self.price_history) > 3000:
            self.price_history.pop(0)

        if self.last_price is None:
            self.last_price = price

    def analyze(self, price: float):
        if self.last_price is None:
            self.last_price = price
            return None

        change = (price - self.last_price) / self.last_price

        signal = None
        if change > self.threshold:
            signal = "BUY"
        elif change < -self.threshold:
            signal = "SELL"

        self.last_price = price
        return signal

    def get_indicator_values(self):
        if len(self.price_history) < 2:
            return {}

        return {
            "last_price": self.price_history[-1],
            "count": len(self.price_history)
        }
