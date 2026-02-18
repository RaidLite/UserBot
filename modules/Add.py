from telethon import events

def a(client):
    @client.on(events.NewMessage(pattern=r'\.dump', outgoing=True))
    async def dump_to_saved(event):
        reply_msg = await event.get_reply_message()

        if reply_msg and reply_msg.photo:
            try:
                await event.client.send_file('me', reply_msg.photo)
                await event.delete()
            except Exception as e:
                print(f"Ошибка при дампе: {e}")
        else:
            await event.delete()