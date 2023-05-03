import pandas as pd
import pybit
import datetime
import requests
import time
import calendar
import re
import numpy as np
from datetime import datetime, timedelta, timezone
from pybit import usdt_perpetual
from FUNCTIONS import get_base_currency, get_price_scale, get_min_price

##########################
coppia = "APEUSDT"
qty_usd = 5
timeframe_inMinuti = 5
atr_coefficent = 1
##########################

# PART 1 | Get the data

base_currency = get_base_currency(coppia)
price_scale = get_price_scale(base_currency)
min_price = get_min_price(base_currency)
entry_price = 0
while True:
    now = datetime.utcnow()
    unixtime = calendar.timegm(now.utctimetuple())
    since = unixtime
    start = str(since - 60 * 200 * int(timeframe_inMinuti))

    # Download DataFrame actual TimeFrame
    url = (
        "https://api.bybit.com/public/linear/kline?symbol="
        + coppia
        + "&interval="
        + str(timeframe_inMinuti)
        + "&from="
        + str(start)
    )

    data = requests.get(url).json()
    D = pd.DataFrame(data["result"])

    marketprice = "https://api.bybit.com/v2/public/tickers?symbol=" + coppia

    res = requests.get(marketprice)
    data = res.json()

    # Get Marketprice, Bidprice, Askprice etc
    try:
        lastprice = float(data["result"][0]["mark_price"])
        ask_price = float(data["result"][0]["ask_price"])
        bid_price = float(data["result"][0]["bid_price"])
        qty_coin = round(qty_usd / lastprice, min_price)
    except:
        time.sleep(2)
        lastprice = float(data["result"][0]["mark_price"])
        ask_price = float(data["result"][0]["ask_price"])
        bid_price = float(data["result"][0]["bid_price"])
        qty_coin = round(qty_usd / lastprice, min_price)

    # Calculate ATR on Chart Time Frame
    high_low = D["high"] - D["low"]
    high_close_prev = np.abs(D["high"] - D["close"].shift())
    low_close_prev = np.abs(D["low"] - D["close"].shift())
    df = D["close"]
    df_atr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1)
    true_range = np.max(df_atr, axis=1)
    atr = true_range.rolling(window=14).mean()
    last_atr = atr.iloc[-1]
    print("ATR is", last_atr)

    # Calculate EMA
    ema200 = D["close"].ewm(span=200, adjust=False).mean()
    last_ema200 = ema200.iloc[-1]
    print("EMA200 is", last_ema200)
    print("")

    # Calculate MACD
    ema12 = D["close"].ewm(span=12, adjust=False).mean()
    ema26 = D["close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    last_macd = macd.iloc[-1]
    last_macd = round(last_macd, 4)
    prev_macd = macd.iloc[-2]
    prev_macd = round(prev_macd, 4)
    signal_line = macd.ewm(span=9, adjust=False).mean()
    last_signal = signal_line.iloc[-1]
    last_signal = round(last_signal, 4)
    prev_signal = signal_line.iloc[-2]
    prev_signal = round(prev_signal, 4)
    print("Prev MACD is", prev_macd)
    print("MACD is", last_macd)
    print("Prev signal Line is", prev_signal)
    print("Signal Line is", last_signal)
    print("----------------------------")

    # PART 2 | Program
    session_auth = usdt_perpetual.HTTP(
        endpoint="https://api.bybit.com",
        api_key="",
        api_secret="",
    )

    # Get actual posizion size
    positionSize = session_auth.my_position(symbol=coppia)
    positionSize_buy = positionSize["result"][0]["size"]
    positionSize_sell = positionSize["result"][1]["size"]
    try:
        last_order = session_auth.get_active_order(symbol=coppia, limit=1)
        last_order_status = last_order["result"]["data"][0]["order_status"]
    except:
        last_order_status = "Null"

    # Check if there are any opened position or order
    if positionSize_buy == 0 and positionSize_sell == 0 and last_order_status != "New":
        # Check if price is above EMA200 and MACD and signal line are under istogram
        if lastprice > last_ema200 and last_macd < 0 and last_signal < 0:
            # Check if there is a cross
            if prev_macd < prev_signal and last_macd >= last_signal:
                # Calculate SL with ATR
                stop_loss = round(lastprice - (last_atr * atr_coefficent), price_scale)
                take_profit = round(
                    lastprice + (last_atr * (atr_coefficent * 2)), price_scale
                )
                # Open LONG position
                session_auth.place_active_order(
                    symbol=coppia,
                    order_type="Limit",
                    price=ask_price,
                    side="Buy",
                    qty=qty_coin,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
                entry_price = ask_price
                print(" ")
                print("OPENED LONG POSITION!")
                print(" ")
                time.sleep((timeframe_inMinuti * 60) / 5)

        # Check if price is under EMA200 and MACD and signal line are above istogram
        elif lastprice < last_ema200 and last_macd > 0 and last_signal > 0:
            # Check if there is a cross
            if prev_macd > prev_signal and last_macd <= last_signal:
                # Calculate SL with ATR
                stop_loss = round(lastprice + (last_atr * atr_coefficent), price_scale)
                take_profit = round(
                    lastprice - (last_atr * (atr_coefficent * 2)), price_scale
                )
                # Open SHORT position
                session_auth.place_active_order(
                    symbol=coppia,
                    order_type="Limit",
                    price=bid_price,
                    side="Sell",
                    qty=qty_coin,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
                entry_price = bid_price
                print(" ")
                print("OPENED SHORT POSITION!")
                print(" ")
                time.sleep((timeframe_inMinuti * 60) / 5)

    # Move SL near entry (LONG)
    elif positionSize_buy != 0 and lastprice > entry_price and entry_price != 0:
        atr_div = round(last_atr / 20, min_price)
        sl_safe = entry_price + atr_div
        session_auth.set_trading_stop(symbol=coppia, side="Buy", stop_loss=sl_safe)
        entry_price = 0
        print("STOP LOSS moved near Entry Price !")

    # Move SL near entry (SHORT)
    elif positionSize_sell != 0 and lastprice < entry_price and entry_price != 0:
        atr_div = round(last_atr / 20, min_price)
        sl_safe = entry_price - atr_div
        session_auth.set_trading_stop(symbol=coppia, side="Sell", stop_loss=sl_safe)
        entry_price = 0
        print("STOP LOSS moved near Entry Price !")
