import argparse
import asyncio

from astropy.time import Time
from lsst.ts import salobj


def print_heartbeat(data):
    htime = Time(data.private_sndStamp, format='unix_tai', scale='tai')
    print(f"Got heartbeat ({data.private_seqNum}): {htime.utc.iso}")


async def main(opts):
    async with salobj.Domain() as domain:
        await asyncio.sleep(5)
        remote = salobj.Remote(domain, "GenericCamera", index=opts.index)
        await remote.start_task
        print("Remote ready")
        remote.evt_heartbeat.callback = print_heartbeat

        while True:
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default=1, type=int, help="Set the index of the camera.")
    args = parser.parse_args()

    asyncio.run(main(args))
