import re
from khl.card import CardMessage, Card, Element, Module, Types

action_theme = {
    "created": Types.Theme.SUCCESS,
    "opened": Types.Theme.SUCCESS,
    "synchronize": Types.Theme.SUCCESS,
    "ready_for_review": Types.Theme.SUCCESS,
    "closed": Types.Theme.SECONDARY,
    "edited": Types.Theme.WARNING,
    "converted_to_draft": Types.Theme.WARNING,
    "deleted": Types.Theme.DANGER,
}

def github_message_card(event: str, sender, body, info=None, theme=None, color=None) -> CardMessage:
    """
    Github事件卡片生成函数
    """
    title = f"New {event.replace('_', ' ').title()} Event from Github"
    sender_name = f"[{sender['login']}]({sender['html_url']})"

    if info:
        sender_name = f"{sender_name}\n{info}"

    if not theme:
        theme = Types.Theme.INFO

    card = Card(
        Module.Header(title),
        Module.Divider(),
        Module.Section(Element.Text(sender_name, Types.Text.KMD), Element.Image(sender["avatar_url"], size=Types.Size.SM, circle=True)),
        theme=theme,
        color=color,
        size=Types.Size.LG
    )

    for message in body:
        card.append(Module.Section(message))

    return CardMessage(card)

def md_to_kmd(str: str) -> str:
    """
    将Markdown字符串转化为符合kmd的字符串
    """
    # str = str.replace("\r\n", "\n")

    while str.find('\n\n') > 0:
        str = str.replace('\n\n', '\n')

    pattern1 = re.compile(r"(__)([^\s\n]+)(__)")
    str = pattern1.sub(r"**\2**", str)

    pattern2 = re.compile(r'_([^\s\n]+)_')
    str = re.sub(pattern2, r'*\1*', str)

    return str

def get_repo_info(data, branch=None):
    repo = data["repository"]
    branch_full_name = repo_full_name = repo["full_name"]
    branch_url = repo_url = repo["html_url"]
    repo_name_url = f"[{repo_full_name}]({repo_url})"

    if branch:
        branch_full_name = f"{repo_full_name}:{branch}"
        branch_url = repo_url if repo["default_branch"] == branch else f"{repo_url}/tree/{branch}"

    return repo_name_url, branch_full_name, branch_url

async def ping(data):
    return "Success", 200

async def push(data):
    if data["deleted"]:
        return "Messages that do not need to be sent", 200

    commits, branch = data['commits'], data["ref"][11:],
    repo_name_url, branch_full_name, branch_url = get_repo_info(data, branch)

    info = f"[{branch_full_name}]({branch_url}) **{len(commits)} new commits**"

    before_hash, after_hash = data['before'][0:7], data['after'][0:7]
    messages = [f"Compare: [{before_hash} -> {after_hash}]({data['compare']})"]
    for commit in commits:
        message, author = commit["message"], commit["author"]

        message = message.replace('\n\n', ' :\n', 1)
        md_to_kmd(message)
        if len(message) > 45 or message.find('\n') > 0:
            message = f"\n{message}"

        hash = commit['id'][0:7]
        messages.append(f"[{hash}]({commit['url']}) from [{author['username']}](https://github.com/{author['username']}): {message}")

    return {"info": info, "messages": messages, "color": "#aaaaaa"}

async def branch_change(data, message, theme=Types.Theme.INFO, deleted=False):
    branch = data["ref"]
    repo_name_url, branch_full_name, branch_url = get_repo_info(data, branch)
    messages = [f"{repo_name_url} **{message}:** [{branch}]({branch_url})" if not deleted
                else f"{repo_name_url} **{message}: {branch}**"]

    return {"messages": messages, "theme": theme}

async def create(data):
    if data["ref_type"] == "branch":  # create branch
        return await branch_change(data, "New branch created")
    else:
        return "Unsupported github event!", 400

async def delete(data):
    if data["ref_type"] == "branch":
        return await branch_change(data, "Branch deleted", theme=Types.Theme.DANGER, deleted=True)
    else:
        return "Unsupported github event!", 400

async def pull_request(data):
    action = data["action"]
    number = data["number"]
    pull_request = data["pull_request"]
    repo_name_url, branch_full_name, branch_url = get_repo_info(data)

    info = f"{repo_name_url} **[Pull request {action.replace('_', ' ')}: #{number}]({pull_request['html_url']})**"

    message = f"**{'Draft: ' if pull_request.get('draft') else ''}{pull_request['title']}**"

    if pull_request.get("body"):
        message = f"{message}\n> {md_to_kmd(pull_request['body'])}"

    return {"info": info, "messages": [message], "theme": action_theme.get(action)}

async def action_event(data, key, event):
    action = data["action"]
    event_data = data[key]
    repo_name_url, branch_full_name, branch_url = get_repo_info(data)

    info = f"{repo_name_url} **[{event.replace('_', ' ')} {action.replace('_', ' ')}]({event_data['html_url']})**"

    if event_data.get("body"):
        message = f"{md_to_kmd(event_data['body'])}"
    else:
        message = info
        info = None

    return {"info": info, "messages": [message], "theme": action_theme.get(action)}

async def pull_request_review(data):
    return await action_event(data, "review", "pull_request_review")

async def commit_comment(data):
    return await action_event(data, "comment", "commit_comment")

async def issue_comment(data):
    return await action_event(data, "comment", "issue_comment")

async def issues(data):
    card_data = await action_event(data, "issue", "issue")

    message = card_data["messages"][0]
    card_data["messages"][0] = f"**{data['issue']['title']} #{data['issue']['number']}**\n{message}"

    return card_data

async def repository(data):
    card_data = await action_event(data, "repository", "repository")

    repo_name_url = f"[{data['repository']['full_name']}]({data['repository']['owner']['html_url']})"
    card_data["messages"][0] = f"{repo_name_url} **Repository {data['action'].replace('_', ' ')}**"

    if data["action"] == "transferred":
        sender = data["sender"]
        user = data["changes"]["owner"]["from"]["user"]
        sender_name = f"[{sender['login']}]({sender['html_url']})"
        owner_name = f"[{user['login']}]({user['html_url']})"
        message = f"{owner_name} transfer to {sender_name}"

        card_data["info"] = card_data["messages"][0]
        card_data["messages"][0] = message

    return card_data

async def organization(data):
    action = data["action"]
    organization = data["organization"]

    message = f"**{organization['login']} organization {action.replace('_', ' ')}**"

    return {"messages": [message], "theme": action_theme.get(action)}
