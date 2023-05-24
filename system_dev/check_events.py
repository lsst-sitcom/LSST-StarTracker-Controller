import argparse
import asyncio
import os

from lsst.ts import salobj


def print_event(name):
    def callback(data):
        print(name)
        print(data)
        print(os.linesep)

    return callback


async def main(opts):
    async with salobj.Domain() as domain:
        await asyncio.sleep(5)
        remote = salobj.Remote(domain, "GenericCamera", index=opts.index)
        await remote.start_task
        print("Remote ready")
        remote.evt_startTakeImage.callback = print_event("startTakeImage")
        remote.evt_startIntegration.callback = print_event("startIntegration")
        remote.evt_endIntegration.callback = print_event("endIntegration")
        remote.evt_startReadout.callback = print_event("startReadout")
        remote.evt_endReadout.callback = print_event("endReadout")
        if not opts.no_lfoa:
            remote.evt_largeFileObjectAvailable.callback = print_event(
                "largeFileObjectAvailable"
            )
        remote.evt_endTakeImage.callback = print_event("endTakeImage")
        remote.evt_roi.callback = print_event("roi")
        remote.evt_streamingModeStarted.callback = print_event("streamingModeStarted")
        remote.evt_streamingModeStopped.callback = print_event("streamingModeStopped")

        while True:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index", default=1, type=int, help="Set the index of the camera."
    )
    parser.add_argument(
        "--no-lfoa", action="store_true", help="Don't add LFOA callback."
    )
    args = parser.parse_args()

    asyncio.run(main(args))
