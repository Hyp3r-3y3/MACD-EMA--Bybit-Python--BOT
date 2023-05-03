import pybit
import time
import re

from math import floor, ceil
from pybit import usdt_perpetual

coppia = "APEUSDT"
coin_name = "APE"
profondita_book_order = "3"

session_auth = usdt_perpetual.HTTP(
    endpoint="https://api.bybit.com",
    api_key="",
    api_secret="",
)


def roundDown(n, d=2):
    d = int("1" + ("0" * d))
    return floor(n * d) / d


def get_coin_wallet_balance(base_currency):

    walletCoinBalance = session_auth.get_wallet_balance()
    keys = walletCoinBalance["result"]["balances"]
    # print(keys)
    for i in keys:
        if i["coin"] == base_currency:
            nice_index = i
    free = nice_index["free"]
    free = float(free)
    # arrotonda per difetto
    free = roundDown(free)
    return free


# TAKE DECIMALS OF SYMBOL
def get_decimals(base_currency):

    INFO = session_auth.query_symbol()
    keys_info = INFO["result"]

    for a in keys_info:
        if a["baseCurrency"] == base_currency:
            coin_index = a

    decimals = coin_index["minPricePrecision"]
    index = 0
    for i in decimals:
        index += 1
        if i == ".":
            start = index

    nDecimals = index - start

    return nDecimals


def get_base_currency(coppia):

    INFO = session_auth.query_symbol()
    keys_info = INFO["result"]

    for a in keys_info:
        if a["name"] == coppia:
            coppia_index = a

    base_currency = coppia_index["base_currency"]
    return base_currency


def get_price_scale(base_currency):
    INFO = session_auth.query_symbol()
    keys_info = INFO["result"]

    for a in keys_info:
        if a["base_currency"] == base_currency:
            coin_index = a
    price_scale = coin_index["price_scale"]
    return price_scale


def get_last_price(coppia):

    PriceInfo = session_auth.latest_information_for_symbol(symbol=coppia)
    last_Price = PriceInfo["result"]["lastPrice"]
    last_Price = float(last_Price)
    return last_Price


def compare_to_marketPrice(stop_loss):
    PriceInfo = session_auth.latest_information_for_symbol(symbol=coppia)
    PriceInfo_str = str(PriceInfo)

    # Isolate last price
    last_1 = re.search("lastPrice(.+?)highPrice", PriceInfo_str).group()
    last_Price = re.search("'(\d.+?)'", last_1).group(1)
    print("Last Market Price is " + last_Price)
    print("Stop Loss Price is " + str(stop_loss))
    last_Price = float(last_Price)

    if last_Price <= stop_loss:
        return True
    else:
        return False


def check_if_TP_isOpen(coppia, TP_ID):
    isWorking = session_auth.query_active_order(symbol=coppia, orderId=TP_ID, limit="1")
    isWorking_str = str(isWorking)
    try:
        is_open_1 = re.search("isWorking': (.+?)\}\]\}", isWorking_str).group(1)
        is_open = re.search("\w*", is_open_1).group()
        return is_open
    except AttributeError:
        is_open = False
        return is_open
    if is_open != True:
        is_open = False
        return is_open


def get_minTradeAmount(coppia):
    INFO = session_auth.query_symbol()
    keys_info = INFO["result"]

    for a in keys_info:
        if a["name"] == coppia:
            coppia_index = a

    minTradeAmount = coppia_index["minTradeAmount"]
    minTradeAmount = float(minTradeAmount)
    return minTradeAmount


def get_min_price(base_currency):
    INFO = session_auth.query_symbol()
    keys_info = INFO["result"]

    for a in keys_info:
        if a["base_currency"] == base_currency:
            coin_index = a
    min_price = str(coin_index["lot_size_filter"]["min_trading_qty"])
    index = 0
    start = 0
    for i in min_price:
        index += 1
        if i == ".":
            start = index

    qty_decimals = index - start
    return qty_decimals


get_min_price("APE")
