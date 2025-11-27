from PyQt6.QtCore import QObject, pyqtSignal
from tinkoff.invest import Client, OrderDirection, OrderType, Quotation
from workers.api_worker import find_instrument_by_ticker

class TradeWorker(QObject):
    order_placed = pyqtSignal(str, str)
    order_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.token = None
        
    def set_token(self, token):
        self.token = token.strip()
        
    def place_market_order(self, instrument_id_or_ticker, direction, quantity):
        try:
            with Client(self.token) as client:
                account_id = client.users.get_accounts().accounts[0].id
                instrument_id = find_instrument_by_ticker(client, instrument_id_or_ticker) if isinstance(instrument_id_or_ticker, str) else instrument_id_or_ticker
                order_direction = OrderDirection.ORDER_DIRECTION_BUY if direction == 'BUY' else OrderDirection.ORDER_DIRECTION_SELL
                
                response = client.orders.post_order(
                    instrument_id=instrument_id,
                    quantity=quantity,
                    direction=order_direction,
                    account_id=account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=""
                )
                
                self.order_placed.emit(response.order_id, f"Рыночный ордер: {direction} {quantity} лотов")
        except Exception as e:
            self.order_error.emit(f"Ошибка рыночного ордера: {str(e)}")
            
    def place_limit_order(self, instrument_id_or_ticker, direction, quantity, price):
        try:
            with Client(self.token) as client:
                account_id = client.users.get_accounts().accounts[0].id
                instrument_id = find_instrument_by_ticker(client, instrument_id_or_ticker) if isinstance(instrument_id_or_ticker, str) else instrument_id_or_ticker
                order_direction = OrderDirection.ORDER_DIRECTION_BUY if direction == 'BUY' else OrderDirection.ORDER_DIRECTION_SELL
                
                price_units = int(price)
                price_nano = int((price - price_units) * 1_000_000_000)
                
                response = client.orders.post_order(
                    instrument_id=instrument_id,
                    quantity=quantity,
                    price=Quotation(units=price_units, nano=price_nano),
                    direction=order_direction,
                    account_id=account_id,
                    order_type=OrderType.ORDER_TYPE_LIMIT,
                    order_id=""
                )
                
                self.order_placed.emit(response.order_id, f"Лимитный ордер: {direction} {quantity} лотов по {price}")
        except Exception as e:
            self.order_error.emit(f"Ошибка лимитного ордера: {str(e)}")