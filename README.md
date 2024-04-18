# BangumiNow!

## Usage

### dmhy

Search name of bangumi in `https://share.dmhy.org/`

- Choose *Latest on top* in *Arrange in following order*
- Choose a team in *Search in following team*
- (Optional) Choose a sort in *Search in following sort*

Click RSS button in the webpage, copy its link

Put the link to `config.json` (Reference template file format)

### telegram

Check this gist: <https://gist.github.com/dlaptev/7f1512ee80b7e511b0435d3ba95d88cc>

Put your `token` and `chat_id` to `config.json` (Reference template file format)

### requirements

Install `python python-requests python-xmltodict aria2p`

Install `cronie`, enable it: `sudo systemctl enable --now cronie.service`

### test

```shell
$ chmod +x ./main.py
$ ./main.py
```

### cron

> [crontab command reference (tldr.inbrowser.app)](https://tldr.inbrowser.app/pages/common/crontab)

```shell
$ crontab -e
--- #add
# execute at 0 and 30 minutes every hour
# assume your local repo is ~/git_repos/BangumiNow
0,30 * * * * ~/git_repos/BangumiNow/main.py
---
$ crontab -l
```