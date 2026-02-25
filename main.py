import asyncio
import logging
import os
import qrcode
from pathlib import Path
from typing import Callable
from colorama import init
from pystyle import Colorate, Colors
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from importlib.util import module_from_spec, spec_from_file_location
from cfg import API_ID, API_HASH, BANNER

logging.basicConfig(level=logging.INFO)
init(autoreset=True)

async def create_client(session_name: str):
    os.makedirs("sessions", exist_ok=True)
    session_file = Path("sessions") / session_name
    client = TelegramClient(
        str(session_file),
        API_ID,
        API_HASH
    )
    await client.connect()
    return client

def p(text):
    return print(colored(text) + " ")

def colored(prompt):
    return Colorate.Vertical(Colors.rainbow, prompt)

async def async_input(prompt: str = "") -> str:
    colored_prompt = colored(prompt)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, colored_prompt + " ")

async def call_maybe_async(func: Callable, *args):
    result = func(*args)
    if asyncio.iscoroutine(result):
        await result

async def main():
    cls()
    os.makedirs("sessions", exist_ok=True)
    p(BANNER)

    choice = await async_input("Введи выбор: ")

    match choice:
        case "1":
            await use_registered_account()
        case "2":
            await register_account()
        case "3":
            return
        case _:
            p("Неверный ввод. Введи 1, 2 или 3.")

async def use_registered_account():
    sessions = [f for f in os.listdir("sessions") if f.endswith(".session")]
    if not sessions:
        p("Нет доступных аккаунтов")
        return

    for i, s in enumerate(sessions, 1):
        p(f"{i}. {s}")

    try:
        idx = int(await async_input("Выбери аккаунт: ")) - 1
        if not (0 <= idx < len(sessions)):
            raise ValueError
    except ValueError:
        p("Некорректный номер аккаунта")
        return

    module_path = Path("modules")
    session_name = Path(sessions[idx]).stem
    cc = await create_client(session_name)

    try:
        await load_modules(cc, module_path)
    except KeyboardInterrupt:
        p("\nОстановка...")
    finally:
        await cc.disconnect()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

async def register_account():
    async def reg():
        clear()
        p('РЕГИСТРАЦИЯ НОВОГО АККАУНТА')
        sid = await async_input('Введите любое название для аккаунта (английскими буквами): ')
        client = await create_client(sid)
        try:
            if not await client.is_user_authorized():
                qr = await client.qr_login()
                p("\nОтсканируйте этот QR-код в приложении Telegram:")
                qr_gen = qrcode.QRCode()
                qr_gen.add_data(qr.url)
                qr_gen.make(fit=True)
                qr_gen.print_ascii(invert=True)
                try:
                    await qr.wait()
                except SessionPasswordNeededError:
                    p('\n[!] На аккаунте включен облачный пароль (2FA).')
                    pw = await async_input('Введите ваш пароль: ')
                    await client.sign_in(password=pw)
                p("Вход выполнен!")
            p('Аккаунт успешно сохранен!')
            await async_input('Нажмите клавишу Enter чтобы вернуться в меню...')
        except Exception as e:
            p(f'Произошла ошибка: {e}')
            await async_input('Нажмите клавишу Enter чтобы вернуться в меню...')
        finally:
            await client.disconnect()

    await reg()

async def load_modules(client: TelegramClient, path: Path):
    if not path.is_dir():
        p(f"Папка модулей не найдена: {path}")
        return

    p(f"Аккаунт {client.session.filename} запущен")

    modules = list(path.glob("*.py"))
    active = 0

    for file in modules:
        try:
            spec = spec_from_file_location(file.stem, file)
            if spec is None or spec.loader is None:
                raise ImportError("Не удалось создать spec")

            module = module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "a"):
                p(f"{file.name}: нет функции a(client)")
                continue

            await call_maybe_async(module.a, client)
            active += 1

        except Exception:
            logging.exception(f"Ошибка загрузки модуля {file.name}")

    p(f"Загружено модулей: {active}/{len(modules)}")
    p("Бот работает. Ctrl+C для остановки.")

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        p("Остановка модулей...")

def cls():
    os.system("cls" if os.name == "nt" else "clear")

async def runner():
    while True:
        await main()

if __name__ == "__main__":
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        p("\nЗавершение программы")