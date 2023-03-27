import json

def save_file(file_path, data):
    with open(file_path, "w") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4, separators=(',', ':')))

def load_file(file_path):
    f = open(file_path, 'r', encoding='utf-8')
    data = json.loads(f.read())
    f.close()
    return data

def save_data():
    save_file(repoid_channels_path, repoid_channels)

def remove_channel_by_name(name: str, channel_id: str):
    if name in reponame_channels and channel_id in reponame_channels[name]:
        del reponame_channels[name][channel_id]
        if len(reponame_channels[name]) == 0:
            del reponame_channels[name]

async def add_channel_by_name(name: str, channel_id: str):
    if name not in reponame_channels:
        reponame_channels[name] = {}

    if channel_id in reponame_channels[name]:
        return False

    for _repoid, channels in repoid_channels.items():
        for channel, _name in channels.items():
            if _name == name:
                return False

    reponame_channels[name][channel_id] = True

    return True

async def repo_name_to_id(name: str, id: str):
    if id in repoid_channels and len(repoid_channels[id]) > 0:
        old_name = list(repoid_channels[id].items())[0][1]
        if old_name != name:  # 如果改变仓库名
            if old_name in reponame_channels:
                reponame_channels[name] = reponame_channels.pop(old_name)

            for channel_id in repoid_channels[id]:
                repoid_channels[id][channel_id] = name
                save_data()

    if name in reponame_channels and len(reponame_channels[name]) > 0:
        if id not in repoid_channels:
            repoid_channels[id] = {}

        for channel_id in reponame_channels.pop(name):
            repoid_channels[id][channel_id] = name

        save_data()

async def remove_repo(repoid):
    if repoid in repoid_channels and len(repoid_channels[repoid]) > 0:
        name = list(repoid_channels[repoid].items())[0][1]
        del repoid_channels[repoid]
        if name in reponame_channels:
            del reponame_channels[name]

    save_data()

async def remove_channel(channel_id: str, name=None, repoid=None):
    reslut = False
    if not repoid or not name:
        for _repoid, channels in repoid_channels.items():
            for channel, _name in channels.items():
                if _name == name or repoid == _repoid:
                    name = _name
                    repoid = _repoid
                    break

    if repoid and repoid in repoid_channels:
        if channel_id in repoid_channels[repoid]:
            del repoid_channels[repoid][channel_id]
        if len(repoid_channels[repoid]) == 0:
            del repoid_channels[repoid]
        save_data()
        reslut = True
    else:
        reslut = False

    if name and name in reponame_channels and channel_id in reponame_channels[name]:
        reslut = True
        del reponame_channels[name][channel_id]
        if len(reponame_channels[name]) == 0:
            del reponame_channels[name]

    return reslut


repoid_channels_path = "./save/repoid_channels.json"
config = load_file("./config/config.json")
reponame_channels = {}
repoid_channels = load_file(repoid_channels_path)
