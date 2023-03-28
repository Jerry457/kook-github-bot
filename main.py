import json
import asyncio
import event_handlers
from aiohttp import web
from github_bot import bot
from save_load import config, repoid_channels, repo_name_to_id, remove_repo
from event_handlers import github_message_card

routes = web.RouteTableDef()

@routes.get('/')
async def link_test(request: web.get):  # 测试是否开通成功
    return web.Response(body="hello world", status=200)


@routes.post('/github-webhook')
async def webhook(request: web.Request):
    headers = request.headers
    body = await request.content.read()
    data = json.loads(body.decode('UTF8'))
    event = headers["X-GitHub-Event"]
    target_type = headers["X-GitHub-Hook-Installation-Target-Type"]
    id = headers["X-GitHub-Hook-Installation-Target-ID"]

    if target_type == "organization":
        name = data["organization"]["login"]
        id = str(data["organization"]["id"])
    elif target_type == "repository":
        name = data["repository"]["full_name"]
        id = str(data["repository"]["id"])
    else:
        return web.Response(body="Unsupported type!", status=400)

    await repo_name_to_id(name, id)

    if id not in repoid_channels:  # 无对应频道
        return web.Response(body="Unbind kook Channel", status=400)

    if not hasattr(event_handlers, event):  # 不支持的类型
        print(f"Unsupported github event:{event}")
        return web.Response(body="Unsupported github event!", status=400)

    for channel_id in repoid_channels[id]:
        card_data = await getattr(event_handlers, event)(data)
        if type(card_data) is tuple:  # 不支持的类型
            return web.Response(body=card_data[0], status=card_data[1])

        message_card = github_message_card(event, data["sender"], card_data["messages"], info=card_data.get("info"), theme=card_data.get("theme"), color=card_data.get("color"))
        ch = await bot.client.fetch_public_channel(channel_id)
        await ch.send(message_card)

    if (target_type == "repository" and event == "repository" and data["action"] == "deleted" and data["repository"]["disabled"]) or \
       (target_type == "organization" and event == "organization" and data["action"] == "deleted"):
        await remove_repo(id)  # 删除组织或者仓库

    return web.Response(body="Success", status=200)

async def main():
    await asyncio.gather(web.run_app(app, port=config["post"]), bot.start())


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)

    asyncio.run(main())
