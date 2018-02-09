#!/usr/bin/python3
import json

def main():
    log = json.load(open("log.json"))

    for msg in log:
        if msg['type'][0] == "msg":
            print(msg['text'])
            print()

if __name__ == "__main__":
    main()
