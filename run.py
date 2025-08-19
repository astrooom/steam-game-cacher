import os
import subprocess
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

DOCKER_IMAGE = os.getenv("STEAMCMD_DOCKER_IMAGE", "steamcmd-bandwidth:latest")
NODE_NAME = os.getenv("NODE_NAME", "unknown")  # Only used for slack notifs.
slack_channel = os.getenv("SLACK_BOT_CHANNEL")
slack_token = os.getenv("SLACK_BOT_TOKEN")
ENABLE_SLACK = slack_channel and slack_token


def setup_logging():
    log_file = os.path.join(os.path.dirname(__file__), 'steamcmd.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )


def send_slack_message(app_id: str, error_str: str):

    text = f"""
    *Failed Steam Game Caching*
    *Details:*
    • *Node Name:* `{NODE_NAME}`
    • *Steam App ID:* `{app_id}`
    • *Error:* `{error_str}`
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {slack_token}",
    }
    payload = {
        "channel": slack_channel,
        "attachments": [
            {
                "color": "#FF0000",
                "text": text,
            },
        ],
    }

    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload)
        res_json = response.json()
    except Exception as error:
        print(f"Slack  Command Notifier: Error sending message - {error}")


def pull_steamcmd():
    """
    Pulls the configured Docker image if it's a remote image, skips if it's a local image.
    """
    logging.info(f"Checking Docker image: {DOCKER_IMAGE}...")

    # Skip pulling for local images (they don't exist in remote registries)
    if not '/' in DOCKER_IMAGE or DOCKER_IMAGE.startswith('steamcmd-bandwidth'):
        logging.info(f"Skipping pull for local image: {DOCKER_IMAGE}")
        return

    # Pull the configured Docker image (only for remote images)
    pull_command = [
        'docker',
        'pull',
        DOCKER_IMAGE,
    ]

    try:
        result = subprocess.run(pull_command, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(
            f"Docker image updated successfully. Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        send_slack_message("Failed to update SteamCMD", str(e))
        logging.error(
            f"Failed to update SteamCMD: {e}. Error output: {e.stderr.decode()}")
        raise

def install_or_update_game(app_id, install_path, interactive, bandwidth_enabled=False, bandwidth_up_rate=None, bandwidth_down_rate=None):

    install_dir = os.path.join(install_path, app_id)

    logging.info(f"Installing/Updating {app_id} to {install_dir}...")
    print(f"Using Docker image: {DOCKER_IMAGE}")
    
    if bandwidth_enabled:
        print(f"Bandwidth limiting enabled:")
        print(f"  - Upload rate: {bandwidth_up_rate or 'unlimited'} KB/s")
        print(f"  - Download rate: {bandwidth_down_rate or 'unlimited'} KB/s")
    else:
        print("Bandwidth limiting disabled")

    # os.makedirs(install_dir, exist_ok=True)

    # Build environment variables for bandwidth limiting
    env_vars = []
    if bandwidth_enabled:
        env_vars.extend(['-e', 'BANDWIDTH_ENABLED=true'])
        if bandwidth_up_rate:
            env_vars.extend(['-e', f'BANDWIDTH_UP_RATE={bandwidth_up_rate}'])
        if bandwidth_down_rate:
            env_vars.extend(['-e', f'BANDWIDTH_DOWN_RATE={bandwidth_down_rate}'])

    command = [
        'docker', 'run',
        '--rm',
        *(["-it"] if interactive else []),
        *(['--privileged'] if bandwidth_enabled else []),
        *env_vars,
        '-v', f'{install_dir}:{install_dir}',
        DOCKER_IMAGE,
        '+force_install_dir', install_dir,
        '+login', 'anonymous',
        '+app_update', app_id, 'validate',
        '+quit'
    ]

    print(f"Running command: {' '.join(command)}")
    
    try:
        # Run without capturing output so we can see it in real-time
        result = subprocess.run(command, check=True)
        logging.info(f"Successfully updated/installed {app_id}")
        print(f"✅ Successfully completed download/update for app {app_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update/install {app_id}: {e}")
        print(f"❌ Failed to download/update app {app_id}: {e}")
        raise


def main(app_ids, install_path, max_workers, interactive, bandwidth_enabled=False, bandwidth_up_rate=None, bandwidth_down_rate=None):
    setup_logging()

    if interactive:
        logging.info(f"Starting the Steam game updater with App IDs {app_ids}")
    else:
        logging.info(
            f"Starting the non-interactive Steam game installer with App IDs {app_ids}")

    if bandwidth_enabled:
        logging.info(f"Bandwidth limiting enabled - Up: {bandwidth_up_rate or 'unlimited'} KB/s, Down: {bandwidth_down_rate or 'unlimited'} KB/s")

    logging.info(f"Checking for latest SteamCMD version...")
    try:
        pull_steamcmd()
    except Exception as e:
        logging.error(f"Error during SteamCMD update: {e}")
        print(f"Error during SteamCMD update: {e}")
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(
            install_or_update_game, app_id, install_path, interactive, bandwidth_enabled, bandwidth_up_rate, bandwidth_down_rate): app_id for app_id in app_ids}

        for future in as_completed(futures):
            app_id = futures[future]
            try:
                future.result()
                print(f"Successfully updated/installed {app_id}")
            except Exception as e:
                logging.error(
                    f"Error during installation/update of {app_id}: {e}")
                send_slack_message(
                    f"Error during installation/update of {app_id}", str(e))
                print(f"Error during installation/update of {app_id}: {e}")


if __name__ == "__main__":

    lockfile = "./lockfile"

    # Check if lockfile exists
    if os.path.exists(lockfile):
        print("Steam game updater is already running. Please wait for it to complete or delete the lockfile. Exiting...")
        sys.exit(1)

    # Create lockfile
    open(lockfile, "w").close()

    try:
        parser = argparse.ArgumentParser(
            description="Install or update Steam games using SteamCMD")
        parser.add_argument('--app_ids', type=str, required=True,
                            help='Comma-separated list of Steam APP_IDs')
        parser.add_argument('--install_path', type=str,
                            required=True, help='Path to install the games')
        parser.add_argument('--max_workers', type=int, default=2,
                            help='Maximum number of concurrent APP IDs to process')
        parser.add_argument('--interactive', type=lambda x: (str(x).lower() == 'true'), default=False,
                            help='Run the SteamCMD docker container in interactive mode (True/False)')
        parser.add_argument('--bandwidth_enabled', type=lambda x: (str(x).lower() == 'true'), default=False,
                            help='Enable bandwidth limiting with Traffic Control (True/False)')
        parser.add_argument('--bandwidth_up_rate', type=int,
                            help='Upload rate limit in KB/s (requires custom Docker image)')
        parser.add_argument('--bandwidth_down_rate', type=int,
                            help='Download rate limit in KB/s (requires custom Docker image)')
        args = parser.parse_args()
        app_ids = args.app_ids.split(',')

        main(app_ids, args.install_path, args.max_workers, args.interactive, 
             args.bandwidth_enabled, args.bandwidth_up_rate, args.bandwidth_down_rate)
    finally:
        # Remove lockfile
        os.remove(lockfile)
