# Requirements

Docker. That's it :P

# Quick Start

## Using Standard SteamCMD Image

```bash
python3 run.py --app_ids=376030,258550 --install_path=/var/lib/steam_cache
```

## Using Custom Image with Bandwidth Limiting

1. Build the custom Docker image with Traffic Control (TC):
```bash
./build-docker.sh
```

2. Set the environment variable to use the custom image:
```bash
export STEAMCMD_DOCKER_IMAGE=steamcmd-bandwidth:latest
```

3. Run with bandwidth limiting:
```bash
python3 run.py --app_ids=376030,258550 --install_path=/var/lib/steam_cache \
               --bandwidth_enabled=true --bandwidth_down_rate=1000
```



## Args

### install_path

The path where the game files will be stored and / or checked on follow-up runs.
Setting `/var/lib/steam_cache` will put each game in `/var/lib/steam_cache/APP_ID`

### app_ids

The Steam APP IDs to install as a comma-separated string.

Get APP IDs from: https://steamdb.info

Be aware that most games have different APP IDs for the game itself and it's dedicated server counterpart.

### max_workers

Maximum number of concurrent APP IDs to process using threading.

### bandwidth_enabled

Enable bandwidth limiting with Traffic Control (requires custom Docker image). Set to `true` or `false`.

### bandwidth_up_rate

Upload rate limit in KB/s. Only works when bandwidth limiting is enabled and using the custom Docker image.

### bandwidth_down_rate

Download rate limit in KB/s. Only works when bandwidth limiting is enabled and using the custom Docker image.

# Custom Docker Image with Traffic Control

This project includes a custom Docker image that extends the official SteamCMD image with TC (Traffic Control) for bandwidth limiting.

## Building the Custom Image

```bash
./build-docker.sh
```

This creates a Docker image named `steamcmd-bandwidth:latest` that includes:
- Official SteamCMD base image
- Traffic Control (TC) bandwidth limiting tools
- Wrapper script for bandwidth-controlled SteamCMD execution

## Using the Custom Image

Set the `STEAMCMD_DOCKER_IMAGE` environment variable:

```bash
# In your shell
export STEAMCMD_DOCKER_IMAGE=steamcmd-bandwidth:latest

# Or in a .env file
echo "STEAMCMD_DOCKER_IMAGE=steamcmd-bandwidth:latest" >> .env
```

## Bandwidth Limiting Examples

Limit download to 1MB/s (1000 KB/s):
```bash
python3 run.py --app_ids=376030 --install_path=/var/lib/steam_cache \
               --bandwidth_enabled=true --bandwidth_down_rate=1000
```

Limit both upload and download:
```bash
python3 run.py --app_ids=376030 --install_path=/var/lib/steam_cache \
               --bandwidth_enabled=true --bandwidth_up_rate=500 --bandwidth_down_rate=1000
```



# Optional Slack Notifications

If you want, you can configure Slack to notify if the script fails to a set channel.

Check these environment variables in the .env

```
SLACK_BOT_CHANNEL=channelName
SLACK_BOT_TOKEN=slackToken
```
