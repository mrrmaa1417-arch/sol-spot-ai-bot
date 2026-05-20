from flask import Flask, request
from openai import OpenAI
import requests
import os
import json

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

@app.route("/test", methods=["GET"])
def test():
    return {"status": "ok"}

@app.route("/tradingview", methods=["POST"])
def tradingview_alert():
    data = request.get_json(silent=True)

    if data:
        raw_text = json.dumps(data, ensure_ascii=False, indent=2)
        symbol = data.get("symbol", "UNKNOWN")
        price = data.get("price", "UNKNOWN")
        interval = data.get("interval", "UNKNOWN")
        signal = data.get("signal", "UNKNOWN")
        trend = data.get("trend", "UNKNOWN")
        time = data.get("time", "UNKNOWN")
        volume = data.get("volume", "UNKNOWN")
        market = data.get("market", "SPOT_ONLY")
        coin_amount = data.get("coin_amount", "57")
        target_profit_usd = data.get("target_profit_usd", "100")
    else:
        raw_text = request.data.decode("utf-8", errors="ignore")
        symbol = "UNKNOWN"
        price = "UNKNOWN"
        interval = "UNKNOWN"
        signal = raw_text
        trend = "UNKNOWN"
        time = "UNKNOWN"
        volume = "UNKNOWN"
        market = "SPOT_ONLY"
        coin_amount = "57"
        target_profit_usd = "100"

    prompt = f"""
أنت محلل تداول فوري Spot فقط.
ممنوع توصيات عقود آجلة.
ممنوع رافعة مالية.
ممنوع Short.
التحليل فقط لشراء وبيع SOL أو العملة المذكورة في السوق الفوري.

بيانات التنبيه من TradingView:
{raw_text}

معلومات مهمة:
- السوق: {market}
- عدد العملات: {coin_amount}
- هدف الربح بالدولار: {target_profit_usd}
- الفريم: {interval}
- السعر الحالي: {price}
- الفوليوم: {volume}

المطلوب:
1- القرار النهائي للفوري فقط: شراء الآن / انتظر / بيع جزئي / بيع كامل
2- هل دخلت سيولة قوية؟ نعم / لا / غير كافية
3- قوة الإشارة من 10
4- سبب القرار باختصار
5- منطقة شراء مناسبة للفوري إذا كانت واضحة
6- منطقة بيع مناسبة لتحقيق الهدف
7- احسب كم يحتاج السعر يرتفع لتحقيق ربح {target_profit_usd} دولار مع {coin_amount} عملة
8- وقف الخسارة أو منطقة الخروج إذا ضعف السعر
9- هل الهدف واقعي الآن أم يحتاج انتظار؟
10- تنبيه مخاطر مختصر

مهم:
إذا البيانات ناقصة أو الإشارة غير واضحة، لا تخترع أرقام.
قل: البيانات غير كافية وانتظر تأكيد.
اكتب بالعربي وبأسلوب واضح ومختصر.
"""

    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=prompt
        )
        ai_analysis = response.output_text
    except Exception as e:
        ai_analysis = f"""
تعذر تشغيل تحليل OpenAI.

السبب:
{str(e)}

لكن وصل تنبيه TradingView بنجاح.
"""

    message = f"""
🚨 SOL Spot AI

العملة: {symbol}
السعر: {price}
الفريم: {interval}
الإشارة: {signal}
الترند: {trend}
الفوليوم: {volume}
الوقت: {time}

{ai_analysis}
"""

    telegram_response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
    )

    return {
        "status": "ok",
        "telegram_status": telegram_response.status_code
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)