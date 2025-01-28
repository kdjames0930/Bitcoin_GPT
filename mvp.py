import os
from dotenv import load_dotenv
load_dotenv()

# 1. 업비트 차트 데이터 가져오기 (30일치 일봉)
import pyupbit
df = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")

# 2. AI에게 데이터 제공하고 판단 받는다.
import json
from openai import OpenAI
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

system_prompt = """
You are an expert in Bitcoin investing. Tell me whether to buy, sell or hold at the moment based on the chart data provided. Response in json format.

EXAMPLE INPUT: bitcoin chart data

EXAMPLE JSON OUTPUT:
{
    "decision": "sell",
    "reason": "some technical reason"
}
"""

user_prompt = df.to_json()

messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={
        'type': 'json_object'
    }
)

# AI 판단에 따라 매수/매도 진행

result = json.loads(response.choices[0].message.content)
print(result)
print(result['decision'])

access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
upbit = pyupbit.Upbit(access, secret)

# Buy
if result["decision"] == "buy":
    my_krw = upbit.get_balance("KRW")
    if my_krw*0.9995 > 5000 :
        print(upbit.buy_market_order("KRW-BTC", my_krw*0.9995))
        print("buy, ", result['reason'])
# Sell
if result["decision"] == "sell":
    my_btc = upbit.get_balance("KRW-BTC")
    current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]['ask_price']
    if my_btc * current_price > 5000:
        print(upbit.sell_market_order("KRW-BTC", ))
        print("sell, ", result['reason'])
# Hold
if result["decision"] == "hold":
    print("hold, ", result['reason'])