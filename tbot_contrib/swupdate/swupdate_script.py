import asyncio
import json
import requests
import websockets  # type: ignore
import argparse

url_upload = "http://{}:8080/upload"
url_status = "ws://{}:8080/ws"


async def wait_update_finished(
    swu_file: str, target_ip: str, timeout: int = 300
) -> None:

    print("Wait update finished")

    async def get_finish_messages() -> int:
        async with websockets.connect(url_status.format(target_ip)) as websocket:

            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                except ValueError:
                    data = {"type": "UNKNOWN"}

                if data["type"] == "status":
                    if data["status"] == "START":
                        continue
                    if data["status"] == "RUN":
                        print("Updating starts")
                        continue
                    if data["status"] == "UNKNOWN":
                        continue
                    if data["status"] == "SUCCESS":
                        print("SWUPDATE successful !")
                        return 0
                    if data["status"] == "FAILURE":
                        print("SWUPDATE failed !")
                        return 1
                if data["type"] == "info":
                    print("info")
                    continue

    await asyncio.wait_for(get_finish_messages(), timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("ip")
    parser.add_argument("timeout", type=int)
    args = parser.parse_args()

    print("Start uploading image...")
    try:
        response = requests.post(
            url_upload.format(args.ip), files={"file": open(args.path, "rb")},
        )

        if response.status_code != 200:
            raise Exception(
                "Cannot upload software image: {}".format(response.status_code)
            )

        print(
            "Software image uploaded successfully. Wait for installation to be finished...\n"
        )
        asyncio.sleep(1)
        asyncio.get_event_loop().run_until_complete(
            wait_update_finished(args.path, args.ip, timeout=args.timeout)
        )

    except ValueError:
        print("No connection to host, exit")


if __name__ == "__main__":
    main()
