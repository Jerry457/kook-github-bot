## Kook github机器人

用于推送github事件到kook频道



### 配置

([创建token)](https://developer.kookapp.cn/app/index))，在`config/config.json`写入

机器人token`kook-bot-token(websocket）`， post为机器人开放的端口

在github webhook填入链接:`https://<ip>/github-webhook`， `Content type`选择`application/json`





### 机器人指令

`/github_bind full_name` `full_name`  绑定该仓库到频道，将在下一次推送事件时自动保存

`/github_debind full_name` 解除绑定仓库
