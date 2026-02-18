from io import BytesIO

import httpx
from telethon import events

WRITE_TEXT = "Введите текст."
TEXTING = "Печатает..."
LOADING = "Загрузка..."
ERROR = "Не удалось получить изображение."


def a(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.write\s+(.+)'))
    async def write_command_handler(event):
        try:
            args = event.pattern_match.group(1)
            if not args:
                await event.edit(WRITE_TEXT)
                return

            message = await event.edit(TEXTING)

            text_for_image = args.replace(" ", "+")
            api_url = f"https://apis.xditya.me/write?text={text_for_image}"

            await message.edit(LOADING)

            async with httpx.AsyncClient(timeout=30.0) as client_http:
                response = await client_http.get(api_url)
                if response.status_code == 200:
                    file_bytes = BytesIO(response.content)
                    file_bytes.name = "photo.jpg"
                    await client.send_file(
                        event.chat_id,
                        file=file_bytes,
                        force_document = False
                    )
                    await message.delete()
                else:
                    await message.edit(ERROR)
        except Exception as e:
            print(f"Ошибка {e}")
            await event.delete()
