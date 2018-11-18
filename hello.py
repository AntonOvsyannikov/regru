import asyncio
import time

start_time = time.time()


async def find_div(what, by):
    print("find_div({}, {}) started".format(what, by))
    a = []
    for i in range(what):
        if i % by == 0:
            a.append(i)
        if i % 10000 == 0:
            await asyncio.sleep(0)
    res = len(a)
    print("find_div({}, {}) finished, {} numbers found".format(what, by, res))

    return res


async def main():
    a = loop.create_task(find_div(22345678, 12345))
    b = loop.create_task(find_div(2341233, 54321))
    c = loop.create_task(find_div(123456, 43210))

    await asyncio.wait([a, b, c])



loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

print("--- %s seconds ---" % (time.time() - start_time))
