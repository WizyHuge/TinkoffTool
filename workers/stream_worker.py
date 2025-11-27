import threading
from PyQt6.QtCore import QObject, pyqtSignal
from tinkoff.invest import Client, TradeInstrument, LastPriceInstrument
from workers.api_worker import find_instrument_by_ticker, quotation_to_float

class MarketStreamWorker(QObject):
    candle = pyqtSignal(float)
    error = pyqtSignal(str)
    started = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.token = None
        self.manager = None

    def set_token(self, token):
        self.token = token.strip()

    def start_stream(self, ticker_or_uid, days=30):
        def run():
            try:
                with Client(self.token) as client:
                    if len(ticker_or_uid) == 36:
                        instrument_id = ticker_or_uid.strip()
                    else:
                        instrument_uid = find_instrument_by_ticker(client, ticker_or_uid.strip())
                        if not instrument_uid:
                            self.error.emit(f"Инструмент '{ticker_or_uid}' не найден")
                            self.stopped.emit()
                            return
                        instrument_id = instrument_uid

                    stream = client.create_market_data_stream()
                    stream.trades.subscribe([TradeInstrument(instrument_id=instrument_id)])
                    stream.last_price.subscribe([LastPriceInstrument(instrument_id=instrument_id)])

                    self.manager = stream
                    self.started.emit()

                    for event in stream:
                        if hasattr(event, 'trade') and event.trade:
                            price = quotation_to_float(event.trade.price)
                            if price: self.candle.emit(price)
                        elif hasattr(event, 'last_price') and event.last_price:
                            price = quotation_to_float(event.last_price.price)
                            if price: self.candle.emit(price)

                    self.stopped.emit()

            except Exception as e:
                self.error.emit(f"Ошибка стрима: {e}")
                self.stopped.emit()

        threading.Thread(target=run, daemon=True).start()

    def stop_stream(self):
        if self.manager:
            self.manager.stop()