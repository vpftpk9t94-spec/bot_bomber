import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiohttp import web

BOT_TOKEN="8739328579:AAG_Od392ucuf2X7QBrxf3pg8vK_nAhko6w"
ADMIN_IDS = [123456789]  # 5562007227

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bomber")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
active_tasks = {}

def is_admin(uid):
    return uid in ADMIN_IDS

@dp.message(Command("start"))
async def start(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("⛔ Нет доступа.")
        return
    await m.answer(
        "💣 <b>TG-BOMBER</b>\n\n"
        "/bomb &lt;user_id&gt; &lt;count&gt; &lt;text&gt;\n"
        "/stop — стоп\n"
        "/status — статус",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("bomb"))
async def bomb(m: Message):
    if not is_admin(m.from_user.id):
        return
    args = m.text.split(maxsplit=3)
    if len(args) < 4:
        await m.answer("❌ /bomb <user_id> <count> <text>")
        return
    try:
        target = int(args[1])
        count = int(args[2])
        text = args[3]
    except ValueError:
        await m.answer("❌ user_id и count — числа.")
        return
    if count < 1 or count > 500:
        await m.answer("❌ count 1..500")
        return
    cid = m.chat.id
    if cid in active_tasks:
        await m.answer("⚠️ Уже идёт. /stop")
        return
    await m.answer(f"🚀 target={target} count={count}")
    active_tasks[cid] = asyncio.create_task(loop(cid, target, count, text))

async def loop(cid, target, count, text):
    sent = 0
    failed = 0
    for i in range(1, count + 1):
        try:
            await bot.send_message(target, text)
            sent += 1
        except Exception as e:
            failed += 1
            s = str(e).lower()
            if "flood" in s or "retry" in s or "too many" in s:
                await asyncio.sleep(30)
        await asyncio.sleep(0.5)
    try:
        await bot.send_message(cid, f"✅ Отправлено: {sent}, ошибок: {failed}")
    except Exception:
        pass
    active_tasks.pop(cid, None)

@dp.message(Command("stop"))
async def stop(m: Message):
    if not is_admin(m.from_user.id):
        return
    t = active_tasks.pop(m.chat.id, None)
    if t:
        t.cancel()
        await m.answer("🛑 Остановлено.")
    else:
        await m.answer("ℹ️ Нет активных задач.")

@dp.message(Command("status"))
async def status(m: Message):
    if not is_admin(m.from_user.id):
        return
    await m.answer("⏳ Активна" if m.chat.id in active_tasks else "💤 Пусто")

async def main():
    # Веб-сервер-заглушка, чтобы Render видел открытый порт
    port = int(os.environ.get("PORT", 10000))
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="OK"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    log.info(f"Бот запущен, порт {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
