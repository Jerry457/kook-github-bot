from khl import Bot, Message, MessageTypes, GuildUser
from khl.card import CardMessage, Card, Module, Types
from save_load import config, add_channel_by_name, remove_channel

bot = Bot(token=config["token"])

async def has_channel_permission(user: GuildUser, guild_id: str) -> bool:
    user.guild_id = guild_id
    for role in await user.fetch_roles():
        if role.permissions & 63 != 0:  # bitValue see https://developer.kaiheila.cn/doc/http/guild-role#%E6%9D%83%E9%99%90%E8%AF%B4%E6%98%8E
            return True
    return False

async def bindfn(msg: Message, full_name, fn, success_message: tuple, fail_message: str):
    error_message = None

    if not msg.ctx.guild:
        error_message = "请在服务器频道中使用命令"
    elif not await has_channel_permission(msg._author, msg.ctx.guild.id):
        error_message = "您的权限不足"
    elif not type(full_name) is str:
        error_message = "传入指令错误"

    channel = msg.ctx.channel
    channel_id = channel.id

    if error_message:
        cardmessage = CardMessage(Card(Module.Section(error_message), theme=Types.Theme.WARNING))
        await channel.send(cardmessage, type=MessageTypes.KMD)
        return

    success = await fn(full_name, channel_id)

    if success:
        cardmessage = CardMessage(
            Card(Module.Section(f"**{success_message[0]}[{full_name}](https://github.com/{full_name})**至(chn){channel_id}(chn){success_message[1]}"), theme=Types.Theme.SUCCESS)
        )
    else:
        cardmessage = CardMessage(Card(Module.Section(fail_message), theme=Types.Theme.WARNING))

    await channel.send(cardmessage, type=MessageTypes.KMD)


@bot.command(name="github_bind")
async def bind(msg: Message, full_name=None):
    await bindfn(msg, full_name, add_channel_by_name, ("成功记录", "，将在下一次推送事件时自动绑定"), "已绑定该存储库，请勿重复绑定")

@bot.command(name="github_debind")
async def debind(msg: Message, full_name=None):
    await bindfn(msg, full_name, lambda full_name, channel_id: remove_channel(channel_id, name=full_name), ("成功取消订阅", ""), "无法找到改存储库，请确认输入正确")
