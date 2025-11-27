import database

cache = {}

def load_cache():
    global cache
    if not cache:
        cache = database.get_all_cached_instruments()
    return cache

def get_cached_tickers():
    return database.get_cached_instrument_ticker()

def get_cached_name(instrument_uid):
    return database.get_cached_instrument(instrument_uid)


def get_cached_ticker(instrument_uid):
    return database.get_cached_ticker(instrument_uid)


def cache_name(instrument_uid, name, ticker=None):
    database.cache_instrument(instrument_uid, name, ticker=ticker)
    global cache
    if not cache:
        cache = {}
    cache[instrument_uid] = name
