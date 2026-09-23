import asyncio
import os
import discord
from discord.ext import commands
from flask import Flask
import threading
import yt_dlp

# --- 1. سيرفر Keep Alive لإبقاء الخدمة تعمل على Render ---
app = Flask('')

@app.route('/')
def home():
    return "Arabic Music Bots 24/7 are Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()

# --- 2. إعدادات الصوت والبوتات ---
BOT_TOKENS = [
    os.getenv(f"TOKEN_{i}") for i in range(1, 11)
]

FFMPEG_BASE_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True
}

bot_data = {}

async def run_bot(token, index):
    if not token:
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    prefixes = [
        f"ش{index}", f"ص{index}", f"مسرع{index}", f"بطيء{index}", f"عادي{index}", f"ثبات{index}",
        "ش ", "ص ", "مسرع", "بطيء", "عادي", "ثبات"
    ]
    bot = commands.Bot(command_prefix=prefixes, intents=intents)
    
    bot_data[index] = {
        'volume': 0.5,
        'speed': '1.0',
        'current_url': None
    }

    @bot.event
    async def on_ready():
        print(f"✅ البوت رقم {index} شغال باسم: {bot.user}")

    # --- ثبات وإعادة توصيل تلقائي إذا انفصل البوت ---
    @bot.event
    async def on_voice_state_update(member, before, after):
        if member == bot.user and before.channel and not after.channel:
            try:
                await before.channel.connect(reconnect=True, self_deaf=True)
                print(f"🔄 إعادة توصيل البوت {index} بالروم الصوتية...")
            except Exception as e:
                print(f"⚠️ تعذر إعادة التوصيل للبوت {index}: {e}")

    def play_audio(ctx, url, volume, speed):
        filter_opt = f"-filter:a \"atempo={speed}\""
        options = f"{FFMPEG_BASE_OPTS['options']} {filter_opt}"
        
        source = discord.FFmpegPCMAudio(url, before_options=FFMPEG_BASE_OPTS['before_options'], options=options)
        vol_source = discord.PCMVolumeTransformer(source, volume=volume)
        
        def after_playing(error):
            if error:
                print(f"Error in Bot {index}: {error}")

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(vol_source, after=after_playing)

    # --- أمر الثبات بالروم ---
    @bot.command(name="ثبات", aliases=[f"ثبات{index}"])
    async def stay_in_vc(ctx):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي الأول عشان يثبت البوت عندك!")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect(reconnect=True, self_deaf=True)
            await ctx.send(f"📌 **البوت {index}**: تم الدخول والتثبيت في الروم **{channel.name}** بنجاح (24/7).")
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"📌 **البوت {index}**: تم نقل وتثبيت البوت في الروم **{channel.name}**.")
        else:
            await ctx.send(f"📌 **البوت {index}**: مثبت بالفعل في الروم.")

    @bot.command(name="ش", aliases=[f"ش{index}"])
    async def play(ctx, *, search: str):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في روم صوتي الأول!")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect(reconnect=True, self_deaf=True)
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                if not search.startswith("http"):
                    search = f"ytsearch:{search}"
                info = ydl.extract_info(search, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                audio_url = info['url']
                title = info.get('title', 'مقطع صوتي')

            bot_data[index]['current_url'] = audio_url
            play_audio(ctx, audio_url, bot_data[index]['volume'], bot_data[index]['speed'])

        await ctx.send(f"🎶 **البوت {index}**: جاري تشغيل **{title}**")

    @bot.command(name="ص", aliases=[f"ص{index}"])
    async def volume(ctx, vol: int):
        if not (0 <= vol <= 200):
            await ctx.send("❌ اختر مستوى صوت بين 0 و 200")
            return
        
        new_vol = vol / 100.0
        bot_data[index]['volume'] = new_vol
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = new_vol
            
        await ctx.send(f"🔊 **البوت {index}**: تم تغيير مستوى الصوت إلى **{vol}%**")

    @bot.command(name="مسرع", aliases=[f"مسرع{index}"])
    async def speed_up(ctx):
        bot_data[index]['speed'] = '1.3'
        if ctx.voice_client and bot_data[index]['current_url']:
            play_audio(ctx, bot_data[index]['current_url'], bot_data[index]['volume'], '1.3')
            await ctx.send(f"⚡ **البوت {index}**: تم تسريع الصوت (1.3x)")
        else:
            await ctx.send("❌ لا يوجد مقطع شغال حالياً!")

    @bot.command(name="بطيء", aliases=[f"بطيء{index}"])
    async def slow_down(ctx):
        bot_data[index]['speed'] = '0.8'
        if ctx.voice_client and bot_data[index]['current_url']:
            play_audio(ctx, bot_data[index]['current_url'], bot_data[index]['volume'], '0.8')
            await ctx.send(f"🐢 **البوت {index}**: تم تبطيء الصوت (0.8x)")
        else:
            await ctx.send("❌ لا يوجد مقطع شغال حالياً!")

    @bot.command(name="عادي", aliases=[f"عادي{index}"])
    async def normal_speed(ctx):
        bot_data[index]['speed'] = '1.0'
        if ctx.voice_client and bot_data[index]['current_url']:
            play_audio(ctx, bot_data[index]['current_url'], bot_data[index]['volume'], '1.0')
            await ctx.send(f"▶️ **البوت {index}**: تم إرجاع السرعة للطبيعية (1.0x)")
        else:
            await ctx.send("❌ لا يوجد مقطع شغال حالياً!")

    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت رقم {index}: {e}")

async def main():
    tasks = []
    for i, token in enumerate(BOT_TOKENS, 1):
        if token:
            tasks.append(run_bot(token, i))
    await asyncio.gather(*tasks)

from threading import Thread

def keep_alive():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    t = Thread(target=keep_alive)
    t.start()
    asyncio.run(main())
