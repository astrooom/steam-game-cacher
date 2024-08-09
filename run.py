import os
import subprocess
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

DOCKER_IMAGE = "steamcmd/steamcmd:latest"
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
    Pulls the latest SteamCMD image and removes unused Docker images.
    """
    logging.info("Updating SteamCMD...")

    # Pull the latest SteamCMD image
    pull_command = [
        'docker',
        'pull',
        'steamcmd/steamcmd:latest',
    ]

    try:
        result = subprocess.run(pull_command, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(
            f"SteamCMD updated successfully. Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        send_slack_message("Failed to update SteamCMD", str(e))
        logging.error(
            f"Failed to update SteamCMD: {e}. Error output: {e.stderr.decode()}")
        raise

    # List all image IDs for steamcmd/steamcmd
    try:
        list_images_command = [
            'docker', 'images', '-q', 'steamcmd/steamcmd'
        ]
        images_result = subprocess.run(
            list_images_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        image_ids = images_result.stdout.decode().strip().split('\n')

        # Keep the most recent image and remove the others
        if image_ids:
            # The latest pulled image should be the first in the list
            latest_image_id = image_ids[0]
            for image_id in image_ids[1:]:  # Start from the second item
                if image_id and image_id != latest_image_id:
                    remove_image_command = [
                        'docker', 'rmi', '-f', image_id
                    ]
                    subprocess.run(remove_image_command, check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logging.info(
                        f"Removed old SteamCMD image with ID: {image_id}")
    except subprocess.CalledProcessError as e:
        send_slack_message("Failed to remove old SteamCMD images", str(e))
        logging.error(
            f"Failed to remove old SteamCMD images: {e}. Error output: {e.stderr.decode()}")
        raise


def install_or_update_game(app_id, install_path, interactive):

    install_dir = os.path.join(install_path, app_id)

    logging.info(f"Installing/Updating {app_id} to {install_dir}...")

    # os.makedirs(install_dir, exist_ok=True)

    command = [
        'docker', 'run',
        *(["-it"] if interactive else []),
        '-v', f'{install_dir}:{install_dir}',
        DOCKER_IMAGE,
        '+force_install_dir', install_dir,
        '+login', 'anonymous',
        '+app_update', app_id, 'validate',
        '+quit'
    ]

    try:
        result = subprocess.run(command, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(
            f"Successfully updated/installed {app_id}. Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Failed to update/install {app_id}: {e}. Error output: {e.stderr.decode()}")
        raise


def main(app_ids, install_path, max_workers, interactive):
    setup_logging()

    if interactive:
        logging.info(f"Starting the Steam game updater with App IDs {app_ids}")
    else:
        logging.info(
            f"Starting the non-interactive Steam game installer with App IDs {app_ids}")

    logging.info(f"Checking for latest SteamCMD version...")
    try:
        pull_steamcmd()
    except Exception as e:
        logging.error(f"Error during SteamCMD update: {e}")
        print(f"Error during SteamCMD update: {e}")
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(
            install_or_update_game, app_id, install_path, interactive): app_id for app_id in app_ids}

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
        parser.add_argument('--interactive', type=lambda x: (str(x).lower() == 'true'), default=True,
                            help='Run the SteamCMD docker container in interactive mode (True/False)')
        args = parser.parse_args()
        app_ids = args.app_ids.split(',')

        main(app_ids, args.install_path, args.max_workers, args.interactive)
    finally:
        # Remove lockfile
        os.remove(lockfile)
