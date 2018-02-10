import bitmex
import datetime
import time
import _thread
 
#API_KEY = 'Bxv6_Fe4q32NBpPRZB7e5hRt'
#API_SECRET = 'mmyKA0cITGghroSFMUtM46pULsuRdxvgp_LKF0jCscLnbrsu'
API_KEY = 'YV109Til3xUBwcDX36sTwnLH'
API_SECRET = 'w-nY31B7wOJ8SRlJCJ4Rfc6rj0nUnlWfJ1J9g59NPmjsL1KQ'
SYMBOL = 'XBTUSD'
IS_TEST = False
RSI_PERIOD_MINUTE = (1 / 6)
RSI_CALCULATION_PERIOD = 14
client = 0
rsi = 0
 
 
def rsi_thread():
    global client
    global rsi
    prices = []
    while True:
        if len(prices) > RSI_CALCULATION_PERIOD + 1:
            prices.pop(0)
        else:
            prices.append(
                float(client.Quote.Quote_get(symbol=SYMBOL, reverse=True, count=1).result()[0][0]['bidPrice']))
        if len(prices) == RSI_CALCULATION_PERIOD + 1:
            ups = []
            downs = []
            for i in range(1, len(prices)):
                difference = prices[i] - prices[i - 1]
                if difference > 0:
                    ups.append(difference)
                else:
                    ups.append(0)
                if difference < 0:
                    downs.append(abs(difference))
                else:
                    downs.append(0)
 
                ups_average = sum(ups) / len(ups)
                downs_average = sum(downs) / len(downs)
 
                if downs_average == 0:
                    downs_average = 1;
                rs = ups_average / downs_average
                rsi = 100 - (100 / (1 + rs))
 
        time.sleep(RSI_PERIOD_MINUTE * 60)
 
 
def get_rsi():
    return rsi
 
 
def main():
    global client
    print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), 'Starting System...')
    client = bitmex.bitmex(test=IS_TEST, api_key=API_KEY, api_secret=API_SECRET)
    print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), 'Connected To Servers!')
 
    print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), 'System will start in', str(RSI_PERIOD_MINUTE * RSI_CALCULATION_PERIOD), 'minutes.')
    _thread.start_new_thread(rsi_thread, ())
    time.sleep((RSI_PERIOD_MINUTE * RSI_CALCULATION_PERIOD * 60) + RSI_CALCULATION_PERIOD)
    while True:
        print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), 'Current RSI is', str(get_rsi()))
        time.sleep(RSI_PERIOD_MINUTE * 60)
 

if __name__ == "__main__":
    main()
    
