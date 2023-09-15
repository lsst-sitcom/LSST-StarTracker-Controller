import argparse
import pathlib

from astropy.time import Time, TimeDelta

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = f"{DATE_FORMAT}T%H:%M:%S"
DATETIME_MS_FORMAT = f"{DATETIME_FORMAT}.%f"
TICK_FREQUENCY = 1000000000

def main(opts: argparse.Namespace) -> None:

    time_start = Time(opts.time_zero, scale="tai", format="unix_tai")

    with opts.input.expanduser().open() as ifile:
        for line in ifile:
            frame_num, timestamp = line.strip().split(",")
            offset = TimeDelta(
                float(timestamp) / TICK_FREQUENCY, scale="tai", format="sec"
            )
            frame_begin = time_start + offset
            frame_dt = frame_begin.to_datetime()
            print(f"Frame {frame_num}: {frame_dt.isoformat()}")
            print(f"Frame {frame_num}: {frame_begin.strftime(DATETIME_MS_FORMAT)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=pathlib.Path, help="File to make timestamps from")
    parser.add_argument("time_zero", type=float, help="The frame start time")

    args = parser.parse_args()
    main(args)
