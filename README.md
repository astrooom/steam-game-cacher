# Requirements

The script can run anywhere Docker and Python can run.

- Docker
- Python 3.6 >
- Pip

```
apt-get install python3 python3-pip

pip3 install requests --break-system-packages
```

(Debian/Ubuntu)

# Usage

```
python3 run.py --app_ids=376030,258550 --install_path=/var/lib/steam_cache
```

## Args

### install_path

The path where the game files will be stored and / or checked on follow-up runs.
Setting `/var/lib/steam_cache` will put each game in `/var/lib/steam_cache/APP_ID`
This must be a full path.

### app_ids

The Steam APP IDs to install as a comma-separated string.

Get APP IDs from: https://steamdb.info

Be aware that most games have different APP IDs for the game itself and it's dedicated server counterpart.

### max_workers (optional)

Maximum number of concurrent APP IDs to process using threading.

### interactive (optional)

Whether the SteamCMD docker container should run in interactive mode or not. If you are running this script in crontab, you should set --interactive=False as crontab is not an interactive environment.

# Optional Slack Notifications

If you want, you can configure Slack to notify if the script errors.

Check these environment variables in the .env

```
SLACK_BOT_CHANNEL=channelName
SLACK_BOT_TOKEN=slackToken
NODE_NAME="nodeName" # Included in the notification on Slack to differentiate where the script runs.
```

The SLACK_BOT_TOKEN must be gathered by creating a Slack application first: https://api.slack.com/apps
