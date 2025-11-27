from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import QObject, pyqtSignal
from tinkoff.invest import Client, CandleInterval, InstrumentIdType, InstrumentStatus
import cache

def quotation_to_float(quotation):
    if not quotation:
        return None
    return float(quotation.units) + float(quotation.nano) / 1_000_000_000

def get_candle_price(candle):
    if candle.close:
        return quotation_to_float(candle.close)
    elif candle.high:
        return quotation_to_float(candle.high)
    elif candle.low:
        return quotation_to_float(candle.low)
    elif candle.open:
        return quotation_to_float(candle.open)
    return None

def find_instrument_by_ticker(client, ticker):
    try:
        instruments = [
            client.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
            client.instruments.bonds(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
            client.instruments.currencies(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
            client.instruments.etfs(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
            client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments
        ]
        for inst_list in instruments:
            for inst in inst_list:
                if inst.ticker.upper() == ticker.upper():
                    return inst.uid
        return None
    except Exception:
        return None

def get_instrument_category(instrument, name=""):
    if instrument and hasattr(instrument, 'instrument_type'):
        inst_type = instrument.instrument_type
        inst_type_name = inst_type.name if hasattr(inst_type, 'name') else str(inst_type)
        
        if 'BOND' in inst_type_name: return "Облигации"
        elif 'CURRENCY' in inst_type_name: return "Валюта"
        elif 'ETF' in inst_type_name: return "Фонды"
        elif 'SHARE' in inst_type_name or 'STOCK' in inst_type_name: return "Акции"
        elif 'FUTURES' in inst_type_name: return "Фьючерсы"
        elif 'OPTION' in inst_type_name: return "Опционы"

    if name:
        name_lower = name.lower()
        if any(x in name_lower for x in ["офз", "облигаци", "bond"]): return "Облигации"
        elif any(x in name_lower for x in ["рубль", "доллар", "евро", "юань", "лира", "currency"]): return "Валюта"
        elif any(x in name_lower for x in ["фонд", "etf", "пиф", "индекс"]): return "Фонды"
        elif any(x in name_lower for x in ["золото", "серебро", "платина", "палладий"]): return "Драгметаллы"

    return "Акции"

class ApiWorker(QObject):
    connected = pyqtSignal(str)
    error = pyqtSignal(str)
    portfolioData = pyqtSignal(dict)
    historicalPricesLoaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.token = None
    
    def check_token(self, token):
        try:
            with Client(token) as client:
                client.users.get_info()
            return True
        except Exception:
            return False
        
    def set_token(self, token):
        self.token = token.strip()

    def connect_api(self):
        try:
            with Client(self.token) as client:
                accounts = client.users.get_accounts().accounts
                self.connected.emit(f"OK. Аккаунтов: {len(accounts)}")
        except Exception as e:
            self.error.emit(str(e))

    def fetch_portfolio(self):
        with Client(self.token) as client:
            account_id = client.users.get_accounts().accounts[0].id
            portfolio = client.operations.get_portfolio(account_id=account_id)

            positions = []
            for pos in portfolio.positions:
                qty = quotation_to_float(pos.quantity)
                price = quotation_to_float(pos.current_price)
                value = qty * price
                instrument_uid = pos.instrument_uid

                instrument_name = cache.get_cached_name(instrument_uid) if instrument_uid else "?"
                if instrument_uid and not instrument_name:
                    instrument = client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=instrument_uid).instrument
                    instrument_name = instrument.name or instrument.ticker or instrument_uid
                    cache.cache_name(instrument_uid, instrument_name, ticker=instrument.ticker)

                instrument_obj = None
                if instrument_uid:
                    try:
                        instrument_obj = client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=instrument_uid).instrument
                    except Exception:
                        pass

                positions.append({
                    'name': instrument_name,
                    'quantity': qty,
                    'price': price,
                    'value': value,
                    'currency': pos.current_price.currency,
                    'ticker': instrument_obj.ticker if instrument_obj else '',
                    'uid': instrument_uid or '',
                    'category': get_instrument_category(instrument_obj, instrument_name)
                })

            self.portfolioData.emit({
                'account_id': account_id,
                'total_amount': quotation_to_float(portfolio.total_amount_portfolio),
                'currency': portfolio.total_amount_portfolio.currency,
                'positions': positions,
                'total_positions_count': len(positions)
            })

    def fetch_historical_prices(self, ticker_or_uid, days=None, hours=None, interval='1min'):
        try:
            if not self.token:
                self.error.emit("Не установлен токен API")
                return

            instrument = self.get_instrument_info(ticker_or_uid)
            if not instrument:
                self.error.emit(f"Инструмент {ticker_or_uid} не найден")
                return

            interval_mapping = {
                '5sec': CandleInterval.CANDLE_INTERVAL_5_SEC,
                '1min': CandleInterval.CANDLE_INTERVAL_1_MIN,
                '5min': CandleInterval.CANDLE_INTERVAL_5_MIN,
                '15min': CandleInterval.CANDLE_INTERVAL_15_MIN,
                'hour': CandleInterval.CANDLE_INTERVAL_HOUR,
                'day': CandleInterval.CANDLE_INTERVAL_DAY
            }
            
            requested_hours = hours if hours else (days * 24 if days else 24)
            
            if interval == 'auto' or requested_hours > 0:
                if requested_hours <= 2: interval = '5sec'
                elif requested_hours <= 24: interval = '1min'
                elif requested_hours <= 168: interval = '5min'
                elif requested_hours <= 720: interval = '15min'
                elif requested_hours <= 2160: interval = 'hour'
                else: interval = 'day'

            max_periods = {'5sec': 2, '1min': 24, '5min': 120, '15min': 360, 'hour': 2160, 'day': 87600}
            max_hours = max_periods.get(interval, 24)
            hours = min(requested_hours, max_hours)

            to_time = datetime.now(timezone.utc)
            from_time = to_time - timedelta(hours=hours)

            with Client(self.token) as client:
                candles = client.market_data.get_candles(
                    figi=instrument.figi,
                    from_=from_time,
                    to=to_time,
                    interval=interval_mapping.get(interval, CandleInterval.CANDLE_INTERVAL_1_MIN)
                )

            price_data = []
            for candle in candles.candles:
                if not candle.open or not candle.close: continue
                
                timestamp = candle.time.replace(tzinfo=timezone.utc).timestamp()
                
                if interval in ['5sec', '1min', '5min', '15min', '30min']:
                    open_price = quotation_to_float(candle.open)
                    high_price = quotation_to_float(candle.high)
                    low_price = quotation_to_float(candle.low)
                    close_price = quotation_to_float(candle.close)
                    
                    if all([open_price, high_price, low_price, close_price]):
                        price_data.append((timestamp, open_price, high_price, low_price, close_price))
                else:
                    close_price = quotation_to_float(candle.close)
                    if close_price: price_data.append((timestamp, close_price))
            
            if price_data:
                price_data.sort(key=lambda x: x[0])
                self.historicalPricesLoaded.emit(price_data)
            else:
                self.error.emit("Нет данных")
                
        except Exception as e:
            self.error.emit(f"Ошибка загрузки истории: {e}")

    def get_instrument_info(self, ticker_or_uid):
        with Client(self.token) as client:
            try:
                try:
                    instrument = client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=ticker_or_uid).instrument
                    if instrument: return instrument
                except: pass
                
                instrument_uid = find_instrument_by_ticker(client, ticker_or_uid)
                if instrument_uid:
                    return client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=instrument_uid).instrument
                
                return None
            except Exception:
                return None