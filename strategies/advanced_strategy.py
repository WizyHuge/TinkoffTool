from collections import deque
import numpy as np
from scipy import stats
from strategies.base_strategy import BaseStrategy, calculate_rsi, calculate_std

class SmartAdaptiveStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Smart Adaptive Strategy")
        self.signals = deque(maxlen=8)
        self.market_regime = "NEUTRAL"
        self.volatility = 0
        self.trend_strength = 0
        self.adaptive_params = {
            'ema_fast': 6, 'ema_slow': 14, 'ema_trend': 30,
            'rsi_period': 12, 'bb_period': 16, 'momentum_period': 8
        }
        
    def _update_market_regime(self):
        if len(self.price_history) < 25:
            return
            
        prices = np.array(list(self.price_history))
        x = np.arange(len(prices))
        slope, _, r_value, _, _ = stats.linregress(x, prices)
        self.trend_strength = abs(r_value)
        
        if slope > 0.0005 and self.trend_strength > 0.2:
            self.market_regime = "BULLISH"
        elif slope < -0.0005 and self.trend_strength > 0.2:
            self.market_regime = "BEARISH"
        else:
            self.market_regime = "NEUTRAL"
        
        if len(prices) >= 15:
            returns = np.diff(prices) / prices[:-1]
            self.volatility = np.std(returns) * 100
    
    def _adapt_parameters(self):
        if self.market_regime in ["BULLISH", "BEARISH"]:
            self.adaptive_params.update({'ema_fast': 5, 'ema_slow': 12, 'ema_trend': 25})
        else:
            self.adaptive_params.update({'ema_fast': 4, 'ema_slow': 10, 'ema_trend': 20})
        
        if self.volatility > 2.5:
            self.adaptive_params.update({'bb_period': 12, 'rsi_period': 10})
        else:
            self.adaptive_params.update({'bb_period': 16, 'rsi_period': 12})
    
    def _calculate_ema(self, prices, period):
        if len(prices) < period:
            return prices[-1] if prices else 0
        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema
    
    def _calculate_bbands(self, prices, period, std_dev=1.8):
        if len(prices) < period:
            return None, None, None
        price_list = list(prices)[-period:]
        middle = sum(price_list) / period
        std = calculate_std(prices, period)
        if std is None:
            return None, None, None
        return middle + (std * std_dev), middle, middle - (std * std_dev)
    
    def _calculate_macd(self, prices, fast=10, slow=22, signal=7):
        if len(prices) < slow:
            return 0, 0, 0
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        macd_history = list(prices)[-signal:]
        macd_signal = self._calculate_ema(macd_history, signal)
        return macd, macd_signal, macd - macd_signal
    
    def _calculate_stochastic(self, prices, period=12, k_smooth=2):
        if len(prices) < period:
            return 50, 50
        price_list = list(prices)[-period:]
        highest_high = max(price_list)
        lowest_low = min(price_list)
        if highest_high == lowest_low:
            return 50, 50
        current_close = price_list[-1]
        k = 100 * (current_close - lowest_low) / (highest_high - lowest_low)
        return k, k
    
    def calculate_indicators(self):
        if len(self.price_history) < 25:
            return None
            
        prices = list(self.price_history)
        current_price = prices[-1]
        
        ema_fast = self._calculate_ema(prices, self.adaptive_params['ema_fast'])
        ema_slow = self._calculate_ema(prices, self.adaptive_params['ema_slow'])
        ema_trend = self._calculate_ema(prices, self.adaptive_params['ema_trend'])
        
        rsi = calculate_rsi(self.price_history, self.adaptive_params['rsi_period'])
        
        bb_upper, bb_middle, bb_lower = self._calculate_bbands(
            self.price_history, self.adaptive_params['bb_period']
        )
        
        macd, macd_signal, macd_hist = self._calculate_macd(prices)
        stoch_k, stoch_d = self._calculate_stochastic(prices)
        
        momentum = 0
        if len(prices) >= self.adaptive_params['momentum_period'] + 1:
            momentum = current_price - prices[-self.adaptive_params['momentum_period'] - 1]
        
        return {
            'ema_fast': ema_fast, 'ema_slow': ema_slow, 'ema_trend': ema_trend,
            'rsi': rsi or 50, 'bb_upper': bb_upper or current_price * 1.08,
            'bb_middle': bb_middle or current_price, 'bb_lower': bb_lower or current_price * 0.92,
            'macd': macd, 'macd_signal': macd_signal, 'macd_hist': macd_hist,
            'stoch_k': stoch_k, 'stoch_d': stoch_d, 'momentum': momentum, 'price': current_price
        }
    
    def generate_signal(self, indicators):
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        ema_trend = indicators['ema_trend']
        rsi = indicators['rsi']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        stoch_k = indicators['stoch_k']
        momentum = indicators['momentum']
        
        buy_score = sell_score = 0
        
        if ema_fast > ema_slow > ema_trend:
            buy_score += 2
        elif ema_fast < ema_slow < ema_trend:
            sell_score += 2
        
        if macd > macd_signal:
            buy_score += 1
        elif macd < macd_signal:
            sell_score += 1
            
        if rsi < 38 and stoch_k < 25:
            buy_score += 1
        elif rsi > 62 and stoch_k > 75:
            sell_score += 1
            
        if momentum > 0:
            buy_score += 1
        else:
            sell_score += 1
        
        if price <= bb_lower * 1.01:
            buy_score += 1
        elif price >= bb_upper * 0.99:
            sell_score += 1
        
        if self.market_regime == "BULLISH":
            buy_score += 1
        elif self.market_regime == "BEARISH":
            sell_score += 1
        
        if buy_score >= 4 and buy_score > sell_score:
            return "BUY"
        elif sell_score >= 4 and sell_score > buy_score:
            return "SELL"
        
        return None
    
    def analyze(self, current_price):
        self.add_price(current_price)
        
        if len(self.price_history) < 25:
            return None
        
        self._update_market_regime()
        self._adapt_parameters()
        
        indicators = self.calculate_indicators()
        if not indicators:
            return None
        
        signal = self.generate_signal(indicators)
        
        if signal and (not self.signals or self.signals[-1] != signal):
            self.signals.append(signal)
            return signal
        
        return None
    
    def get_indicator_values(self):
        if len(self.price_history) < 25:
            return {}
        
        indicators = self.calculate_indicators()
        if not indicators:
            return {}
        
        return {
            'EMA Fast': round(indicators['ema_fast'], 2),
            'EMA Slow': round(indicators['ema_slow'], 2),
            'RSI': round(indicators['rsi'], 1),
            'MACD': round(indicators['macd'], 3),
            'Stoch K': round(indicators['stoch_k'], 1),
            'Regime': self.market_regime,
            'Volatility': round(self.volatility, 1)
        }
    
    def reset(self):
        super().reset()
        self.signals.clear()
        self.market_regime = "NEUTRAL"
        self.volatility = 0
        self.trend_strength = 0
        
class CostAwareSmartStrategy(SmartAdaptiveStrategy):
    def __init__(self, broker_commission=0.0005):
        super().__init__()
        self.name = "Cost Aware Smart Strategy"
        self.broker_commission = broker_commission
        self.position = None
        self.entry_price = 0
        self.trade_count = 0
        self.total_commission = 0
        self.required_profit_margin = 0.001
        
    def calculate_net_price(self, price, direction):
        return price * (1 + self.broker_commission) if direction == 'BUY' else price * (1 - self.broker_commission)
    
    def calculate_break_even(self, entry_price, direction):
        entry_net = entry_price * (1 + self.broker_commission) if direction == 'BUY' else entry_price * (1 - self.broker_commission)
        return entry_net / (1 - self.broker_commission) if direction == 'BUY' else entry_net / (1 + self.broker_commission)
    
    def analyze(self, current_price):
        self.add_price(current_price)
        
        if len(self.price_history) < 25:
            return None
        
        self._update_market_regime()
        self._adapt_parameters()
        
        indicators = self.calculate_indicators()
        if not indicators:
            return None
        
        raw_signal = self.generate_signal(indicators)
        filtered_signal = self._filter_signal_with_costs(raw_signal, current_price, indicators)
        
        if filtered_signal and (not self.signals or self.signals[-1] != filtered_signal):
            self.signals.append(filtered_signal)
            return filtered_signal
        
        return None
    
    def _filter_signal_with_costs(self, signal, current_price, indicators):
        if signal == "BUY":
            if self.position == 'LONG':
                return None
                
            net_buy_price = self.calculate_net_price(current_price, 'BUY')
            break_even_sell = self.calculate_break_even(current_price, 'BUY')
            
            if indicators['bb_upper'] > break_even_sell * 1.005:
                return "BUY"
            return None
                
        elif signal == "SELL":
            if self.position == 'LONG':
                net_sell_price = self.calculate_net_price(current_price, 'SELL')
                net_buy_price = self.calculate_net_price(self.entry_price, 'BUY')
                profit_percent = (net_sell_price - net_buy_price) / net_buy_price
                
                if profit_percent > self.required_profit_margin or profit_percent < -0.015:
                    return "SELL"
            return None
        
        return signal
    
    def update_position(self, signal, price):
        if signal == "BUY":
            self.position = 'LONG'
            self.entry_price = price
            self.trade_count += 1
            self.total_commission += price * self.broker_commission
            
        elif signal == "SELL" and self.position == 'LONG':
            buy_net = self.calculate_net_price(self.entry_price, 'BUY')
            sell_net = self.calculate_net_price(price, 'SELL')
            self.total_commission += price * self.broker_commission
            self.position = None
    
    def get_indicator_values(self):
        base_indicators = super().get_indicator_values()
        
        if self.position == 'LONG':
            current_net = self.calculate_net_price(self.price_history[-1], 'SELL')
            entry_net = self.calculate_net_price(self.entry_price, 'BUY')
            unrealized_pnl = (current_net - entry_net) / entry_net * 100
            
            base_indicators.update({
                'Position': 'LONG',
                'Entry Price': round(self.entry_price, 2),
                'PnL %': round(unrealized_pnl, 2)
            })
        
        base_indicators.update({
            'Trades': self.trade_count,
            'Commission': round(self.total_commission, 2)
        })
        
        return base_indicators