import json
import time
import itertools

log = json.load(open("log.json"))

testcases = [
    ("U-Boot git repo setup ", "clean_repo_checkout"),
    ("U-Boot build total    ", "@build"),
    ("U-Boot build raw      ", "@compile"),
    ("U-Boot total          ", "build_uboot"),
    ]

# Get testcase begin and end times
t = itertools.chain(
        *map(lambda tc: (time.mktime(time.strptime(e['time']))
                         for e in log
                         if e['type'][0] == 'testcase' and e['name'] == tc[1]),
             testcases))

# Subtract end from start time
t1, t2 = itertools.tee(t, 2)
times = map(lambda x: x[1] - x[0],
            itertools.compress(zip(t1, itertools.islice(t2, 1, None)),
                               itertools.cycle([1, 0])))

# Print values
for name, t in zip(map(lambda tc: tc[0], testcases), times):
    print(f"{name}: {t}s")
