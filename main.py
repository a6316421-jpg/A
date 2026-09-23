
import asyncio
import os
import discord

# قراءة التوكنات الـ 10 من إعدادات Render
BOT_TOKENS = [
    os.getenv(f"TOKEN_{i}") for i in range(1, 11) if os.getenv(f"TOKEN_{i}")
]


async def run_bot(token, index):
    intents = discord.Intents.default()
    intents.voice_states = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ البوت رقم {index} شغال باسم: {client.user}")

    try:
        await client.start(token)
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت رقم {index}: {e}")


async def main():
    if not BOT_TOKENS:
        print(
            "⚠️ لم يتم العثور على أي توكن! تأكد من إضافة TOKEN_1 إلى TOKEN_10 في Render."
        )
        return

    # تشغيل كل البوتات الموجودة بالتوازي
    tasks = [run_bot(token, i + 1) for i, token in enumerate(BOT_TOKENS)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
