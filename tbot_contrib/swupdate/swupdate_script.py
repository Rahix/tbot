import argparse
import asyncio
import json

import requests
import websockets  # type: ignore

URL_UPLOAD = "http://{}:8080/upload"
URL_STATUS = "ws://{}:8080/ws"


async def wait_update_finished(
    swu_file: str, target_ip: str, timeout: int = 300
) -> bool:
    print("Waiting for installation to finish...")

    async def get_finish_messages() -> int:
        async with websockets.connect(URL_STATUS.format(target_ip)) as websocket:
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                except ValueError:
                    data = {"type": "UNKNOWN"}

                # TODO: Parse messages and show a nicer representation.
                print(repr(data))

                if data["type"] == "status":
                    if data["status"] == "START":
                        continue
                    if data["status"] == "RUN":
                        print("Update started.")
                        continue
                    if data["status"] == "UNKNOWN":
                        continue
                    if data["status"] == "SUCCESS":
                        print("SWUPDATE successful!")
                        return True
                    if data["status"] == "FAILURE":
                        print("SWUPDATE failed!")
                        return False
                if data["type"] == "info":
                    print("info")
                    continue

    return await asyncio.wait_for(get_finish_messages(), timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("ip")
    parser.add_argument("timeout", type=int)
    args = parser.parse_args()

    print("Uploading image...")
    try:
        response = requests.post(
            URL_UPLOAD.format(args.ip),
            files={"file": open(args.path, "rb")},
        )

        if response.status_code != 200:
            raise Exception(f"Cannot upload software image: {response.status_code}")

        print("Image uploaded successfully.")
    except ValueError:
        print("No connection to host, exit")

    if not asyncio.run(wait_update_finished(args.path, args.ip, timeout=args.timeout)):
        raise Exception("Error during update.")


if __name__ == "__main__":
    main()
