import argparse
import asyncio
import os
import sys
from lsst.ts import salobj


class Commander:
    def __init__(self, device_name, opts):
        self.opts = opts
        self.device_name = device_name
        self.index = self.opts.index
        self.command = self.opts.command
        self.timeout = self.opts.timeout
        self.overrides = self.opts.overrides
        self.exp_time = self.opts.exp_time
        self.roi = self.opts.roi

    async def run_command(self):
        async with salobj.Domain() as domain, salobj.Remote(
            domain=domain, name=self.device_name, index=self.index
        ) as csc:
            await csc.start_task

            cmd = getattr(csc, f"cmd_{self.command}")
            params = {"timeout": self.timeout}

            if self.command == "start":
                params.update({"configurationOverride": self.overrides})
            elif self.command == "startLiveView":
                params.update({"expTime": self.exp_time})
            elif self.command == "takeImages":
                params.update(
                    {
                        "expTime": self.exp_time,
                        "numImages": self.opts.num_images,
                        "shutter": True,
                        "sensors": "",
                        "keyValueMap": "imageType:TEST",
                        "obsNote": "",
                    }
                )
            elif self.command == "setROI":
                top, left, width, height = [int(x) for x in self.roi.split(",")][:]
                params.update(
                    {
                        "topPixel": top,
                        "leftPixel": left,
                        "width": width,
                        "height": height,
                    }
                )
            elif self.command == "startStreamingMode":
                params.update({"expTime": self.exp_time})

            try:
                await cmd.set_start(**params)
            except Exception as e:
                print(e)

            print("Done")


if __name__ == "__main__":
    name = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(
        prog=name, description="Send SAL commands to devices"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, dest="timeout", default=30, help="command timeout"
    )
    parser.add_argument("--index", type=int, help="Set the CSC index")

    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument(
        "-o", "--overrides", default="", dest="overrides", help="overrides to apply"
    )

    start_live_view_parser = subparsers.add_parser("startLiveView")
    start_live_view_parser.add_argument(
        "-e",
        "--exp-time",
        type=float,
        default=10,
        help="Set the live view exposure time",
    )

    take_images_parser = subparsers.add_parser("takeImages")
    take_images_parser.add_argument(
        "-e", "--exp-time", type=float, default=10, help="Exposure time"
    )
    take_images_parser.add_argument(
        "-n", "--num-images", type=int, default=1, help="Number of exposures to take"
    )

    start_streaming_mode_parser = subparsers.add_parser("startStreamingMode")
    start_streaming_mode_parser.add_argument(
        "-e",
        "--exp-time",
        type=float,
        default=0.011,
        help="Set the streaming mode exposure time",
    )

    roi_parser = subparsers.add_parser("setROI")
    roi_parser.add_argument(
        "-r", "--roi", help="ROI as comma-delimited string: top,left,width,height"
    )

    cmds = [
        "enable",
        "disable",
        "enterControl",
        "exitControl",
        "standby",
        "abort",
        "resetFromFault",
        "stopLiveView",
        "setFullFrame",
        "stopStreamingMode",
    ]

    for x in cmds:
        p = subparsers.add_parser(x)

    args = parser.parse_args()

    if args.command != "start":
        args.overrides = None
    if args.command not in ["startLiveView", "takeImages", "startStreamingMode"]:
        args.exp_time = 0.0
    if args.command != "takeImages":
        args.num_images = 1
    if args.command != "setROI":
        args.roi = None

    cmdr = Commander("GenericCamera", args)
    asyncio.run(cmdr.run_command())
