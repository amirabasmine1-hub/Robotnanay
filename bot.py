import os
import requests

BALE_TOKEN = os.environ["BALE_BOT_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

BALE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL = "llama-3.3-70b-versatile"


def bale_request(method, data):
    response = requests.post(
        f"{BALE_URL}/{method}",
        json=data,
        timeout=30
    )
    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            result.get("description", "Bale API error")
        )

    return result.get("result", [])


def ask_ai(question):
    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "نام تو AMIR AI است. "
                        "یک دستیار هوش مصنوعی فارسی، "
                        "دوستانه، مفید و خوش‌برخورد هستی. "
                        "به زبان کاربر پاسخ بده. "
                        "پاسخ‌ها را واضح و متناسب با سؤال بنویس."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 700
        },
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"].strip()


def send_message(chat_id, text):
    # محدودیت طول پیام را رعایت می‌کنیم.
    text = text[:4000]

    bale_request(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


def process_update(update):
    message = update.get("message")

    if not message:
        return

    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")

    if not text or chat_id is None:
        return

    if text == "/start":
        send_message(
            chat_id,
            "سلام! 🤖💜\n"
            "به AMIR AI خوش اومدی!\n\n"
            "من دستیار هوش مصنوعی تو هستم.\n"
            "هر سؤالی داری بپرس!"
        )
        return

    if text == "/help":
        send_message(
            chat_id,
            "🤖 راهنمای AMIR AI\n\n"
            "هر پیامی بفرستی، تلاش می‌کنم "
            "با کمک هوش مصنوعی بهت جواب بدم.\n\n"
            "دستورها:\n"
            "/start - شروع ربات\n"
            "/help - راهنما"
        )
        return

    try:
        answer = ask_ai(text)

        send_message(
            chat_id,
            answer or "جوابی دریافت نکردم؛ دوباره امتحان کن."
        )

    except Exception as error:
        # جزئیات خطا را به کاربران نمایش نمی‌دهیم.
        print("AI request failed:", type(error).__name__)

        send_message(
            chat_id,
            "فعلاً نتونستم جواب بدم 😕\n"
            "لطفاً کمی بعد دوباره امتحان کن."
        )


def main():
    offset = 0

    # هر اجرا تعداد محدودی پیام را بررسی می‌کند.
    # اجرای بعدی پیام‌های جدید را هم بررسی خواهد کرد.
    for _ in range(10):
        updates = bale_request(
            "getUpdates",
            {
                "offset": offset,
                "timeout": 0,
                "limit": 100
            }
        )

        if not updates:
            break

        for update in updates:
            offset = max(
                offset,
                update["update_id"] + 1
            )

            try:
                process_update(update)
            except Exception as error:
                print(
                    "Message processing failed:",
                    type(error).__name__
                )

    print("AMIR AI run finished.")


if __name__ == "__main__":
    main()
