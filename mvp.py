import os
import json
import time
import pyupbit
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Upbit API 키
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")

# DeepSeek API 설정
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = "https://api.deepseek.com"

if not api_key:
    raise ValueError("DEEPSEEK_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

client = OpenAI(api_key=api_key, base_url=base_url)

# 1. 업비트 데이터 가져오기
df = pyupbit.get_ohlcv("KRW-BTC", count=5, interval="minute1")

# 2. AI 판단 요청
system_prompt = """
You are an expert in Bitcoin investing. Tell me whether to buy, sell or hold at the moment based on the chart data provided. Response in JSON format.

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

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={'type': 'json_object'}
    )
    
    # 응답 확인
    if response and response.choices and response.choices[0].message.content:
        result = json.loads(response.choices[0].message.content)
        print(result)
    else:
        print("API 응답이 비어 있음!")
        result = {"decision": "hold", "reason": "API 응답 없음"}

except Exception as e:
    print(f"API 요청 중 오류 발생: {e}")
    result = {"decision": "hold", "reason": "API 요청 실패"}

# 3. AI 판단에 따른 매매 실행
upbit = pyupbit.Upbit(access, secret)

def trade():
    while True:
        try:
            if result["decision"] == "buy":
                my_krw = upbit.get_balance("KRW")
                if my_krw * 0.9995 > 5000:
                    print(upbit.buy_market_order("KRW-BTC", my_krw * 0.9995))
                    print("buy, ", result['reason'])

            elif result["decision"] == "sell":
                my_btc = upbit.get_balance("KRW-BTC")
                current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]['ask_price']
                if my_btc * current_price > 5000:
                    print(upbit.sell_market_order("KRW-BTC", my_btc))
                    print("sell, ", result['reason'])

            else:
                print("hold, ", result['reason'])

        except Exception as e:
            print(f"거래 실행 중 오류 발생: {e}")

        time.sleep(30)

# 실행
try:
    trade()
except KeyboardInterrupt:
    print("Trade stopped due to user interruption")
