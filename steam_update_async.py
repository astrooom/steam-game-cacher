import os
import subprocess
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


def setup_logging():
    log_file = os.path.join(os.path.dirname(__file__), 'steamcmd.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def send_slack_message(APP_ID: str, Error: str):
    channel = os.getenv("SLACK_BOT_CHANNEL")
    token = os.getenv("SLACK_BOT_TOKEN")

    if not channel or not token:
        return

    text = f"""
    *Failed Game Caching*
    *Details:*
    • *APP_ID:* `{APP_ID}`
    • *Error:* `{Error}`
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "channel": channel,
        "attachments": [
            {
                "color": "#FF0000",
                "text": text,
            },
        ],
    }

    try:
        response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
        res_json = response.json()
    except Exception as error:
        print(f"Slack  Command Notifier: Error sending message - {error}")


def update_steamcmd():
    logging.info("Updating SteamCMD...")
    command = ['steamcmd', '+login', 'anonymous', '+quit']
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"SteamCMD updated successfully. Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update SteamCMD: {e}. Error output: {e.stderr.decode()}")
        raise

def install_or_update_game(app_id, install_path):
    install_dir = os.path.join(install_path, app_id)
    os.makedirs(install_dir, exist_ok=True)
    command = [
        'steamcmd', '+login', 'anonymous', 
        '+force_install_dir', install_dir, 
        '+app_update', app_id, 'validate', 
        '+quit'
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Successfully updated/installed {app_id}. Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update/install {app_id}: {e}. Error output: {e.stderr.decode()}")
        send_slack_message(app_id, e.stderr.decode())
        raise

def main(app_ids, install_path, max_workers):
    setup_logging()
    logging.info("Starting the Steam game updater...")
    
    logging.info(f"Checking for latest SteamCMD version...")
    try:
        update_steamcmd()
    except Exception as e:
        logging.error(f"Error during SteamCMD update: {e}")
        print(f"Error during SteamCMD update: {e}")
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(install_or_update_game, app_id, install_path): app_id for app_id in app_ids}

        for future in as_completed(futures):
            app_id = futures[future]
            try:
                future.result()
                print(f"Successfully updated/installed {app_id}")
            except Exception as e:
                logging.error(f"Error during installation/update of {app_id}: {e}")
                print(f"Failed to update/install {app_id}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install or update Steam games using SteamCMD")
    parser.add_argument('--app_ids', type=str, required=True, help='Comma-separated list of Steam APP_IDs')
    parser.add_argument('--install_path', type=str, required=True, help='Path to install the games')
    parser.add_argument('--max_workers', type=int, default=2, help='Maximum number of concurrent workers to download and install games')

    args = parser.parse_args()
    app_ids = args.app_ids.split(',')
    main(app_ids, args.install_path, args.max_workers)