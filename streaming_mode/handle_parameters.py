import argparse
from typing import Optional
import sys

import vimba


def abort(reason: str, return_code: int = 1):
    print(reason + '\n')

    sys.exit(return_code)


def set_full_frame(cam: vimba.Camera):
    cam.OffsetX.set(0)
    cam.OffsetY.set(0)
    cam.Width.set(cam.WidthMax.get())
    cam.Height.set(cam.HeightMax.get())


def get_camera(camera_id: Optional[str]) -> vimba.Camera:
    with vimba.Vimba.get_instance() as v:
        if camera_id:
            try:
                return v.get_camera_by_id(camera_id)

            except vimba.VimbaCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = v.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')

            return cams[0]


def main(opts: argparse.Namespace) -> None:
    cam_id = opts.device_id
    with vimba.Vimba.get_instance():
        with get_camera(cam_id) as cam:
            feature_attr = getattr(cam, opts.feature)
            current_value = feature_attr.get()
            print(f"Current value of {opts.feature}: {current_value}")
            feature_attr.set(opts.value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("feature")
    parser.add_argument("value")
    parser.add_argument("-i", "--device-id")
    args = parser.parse_args()
    main(args)
