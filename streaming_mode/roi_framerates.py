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

    if opts.roi is not None:
        rois = [[int(x) for x in opts.roi.split(',')]]
    else:
        rois = [[0,0,0,0], [0,0,200,200], [0,0,150,150], [0,0,100,100], [0,0,50,50]]

    with vimba.Vimba.get_instance():
        with get_camera(cam_id) as cam:
            try:
                cam.GVSPAdjustPacketSize.run()

                while not cam.GVSPAdjustPacketSize.is_done():
                    pass

            except (AttributeError, vimba.VimbaFeatureError):
                print("Packet size adjustment failed")
                pass

            if opts.roi is None:
                rois[0][2] = cam.WidthMax.get()
                rois[0][3] = cam.HeightMax.get()

            for roi in rois:
                cam.OffsetX.set(roi[0])
                cam.OffsetY.set(roi[1])
                cam.Width.set(roi[2])
                cam.Height.set(roi[3])

                print(f"Roi size: {roi[2]}x{roi[3]}")
                print(f"Frame rate limit:{cam.AcquisitionFrameRateLimit.get()}")
                print(f"Frame rate abs: {cam.AcquisitionFrameRateLimit.get()}")

            set_full_frame(cam)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--roi")
    parser.add_argument("-i", "--device-id", default="")
    args = parser.parse_args()
    main(args)
