import argparse
import asyncio
import concurrent.futures
from datetime import datetime
import functools
import io
import pathlib
import sys
import time
from typing import Optional

from astropy.io import fits
import numpy as np
from PIL import Image
import vimba


class Driver:
    def __init__(self, device_id: str, exposure_time: int, is_jpeg: bool, roi: str | None, no_save: bool = False):
        self.device_id = device_id
        self.no_save = no_save
        self.num_images: int = 0
        self.start_time: float = 0
        self.end_time: float = 0
        self.exposure_time: int = exposure_time
        self.day_obs = datetime.now().strftime("%Y%m%d")
        self.file_format = "CAM_{0}_{1:07d}.{2}"
        self.loop = asyncio.get_running_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        if is_jpeg:
            self.save_file = self.create_jpeg_file
        else:
            self.save_file = self.create_fits_file
        if roi is None:
            self.use_roi = False
        else:
            self.use_roi = True
            values = [int(x) for x in roi.split(",")]
            self.top = values[0]
            self.left = values[1]
            self.width = values[2]
            self.height = values[3]

    def abort(self, reason: str, return_code: int = 1):
        print(reason + '\n')

        sys.exit(return_code)

    def get_camera(self, camera_id: Optional[str]) -> vimba.Camera:
        with vimba.Vimba.get_instance() as v:
            if camera_id:
                try:
                    return v.get_camera_by_id(camera_id)

                except vimba.VimbaCameraError:
                    self.abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

            else:
                cams = v.get_all_cameras()
                if not cams:
                    self.abort('No Cameras accessible. Abort.')

            return cams[0]

    def setup_camera(self, cam: vimba.Camera):
        with cam:
            # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
            try:
                cam.GVSPAdjustPacketSize.run()

                while not cam.GVSPAdjustPacketSize.is_done():
                    pass

                cam.AcquisitionMode.set("Continuous")
                cam.ExposureAuto.set("Off")
                cam.ExposureTimeAbs.set(self.exposure_time)
                cam.set_pixel_format(vimba.PixelFormat.Mono12)

            except (AttributeError, vimba.VimbaFeatureError):
                pass

            try:
                cam.ChunkModeActive.set(True)
            except (AttributeError, vimba.VimbaFeatureError):
                print("ChunkMode not available.")

            if self.use_roi:
                cam.OffsetX.set(self.left)
                cam.OffsetY.set(self.top)
                cam.Width.set(self.width)
                cam.Height.set(self.height)

    def frame_handler(self, cam: vimba.Camera, frame: vimba.Frame):
        print('{} acquired {}'.format(cam, frame), flush=True)
        self.num_images += 1
        if not self.no_save:
            self.save_file(frame.as_numpy_ndarray(), frame.get_id())
        cam.queue_frame(frame)

    def create_fits_file(self, buffer: np.ndarray, frame_num: int) -> None:
        img_file = pathlib.Path(self.file_format.format(self.day_obs, frame_num, "fits"))
        file_path = pathlib.Path.home() / "data" / img_file
        img = fits.ImageHDU(buffer)
        hdul = fits.HDUList([fits.PrimaryHDU(), img])
        fileobj = io.BytesIO()
        hdul.writeto(fileobj)
        fileobj.seek(0)

        with file_path.open("wb") as ofile:
            ofile.write(fileobj.getbuffer())

    def set_full_frame(self, cam: vimba.Camera):
        cam.OffsetX.set(0)
        cam.OffsetY.set(0)
        cam.Width.set(cam.WidthMax.get())
        cam.Height.set(cam.HeightMax.get())

    def create_jpeg_file(self, buffer: np.ndarray, frame_num: int) -> None:
        img_file = pathlib.Path(self.file_format.format(self.day_obs, frame_num, "png"))
        file_path = pathlib.Path.home() / "data" / img_file
        buffer = buffer.astype(np.uint16)
        img = Image.fromarray(buffer[:, :, 0], mode="L")
        img.save(file_path, "PNG")

    def run(self):
        with vimba.Vimba.get_instance():
            with self.get_camera(self.device_id) as cam:

                self.setup_camera(cam)
                print('Press <enter> to stop Frame acquisition.')
                try:
                    # Start Streaming with a custom a buffer of 10 Frames (defaults to 5)
                    cam.start_streaming(handler=self.frame_handler, buffer_count=10,
                                        allocation_mode=vimba.AllocationMode.AnnounceFrame)
                    self.start_time = time.time()
                    input()

                finally:
                    self.end_time = time.time()
                    cam.stop_streaming()
                    self.set_full_frame(cam)

                total_time = self.end_time - self.start_time
                fps = self.num_images / total_time
                print(f"Total elapsed time: {total_time} seconds")
                print(f"TOtal number of images: {self.num_images}")
                print(f"FPS = {fps}")

async def main(opts: argparse.Namespace) -> None:
    d = Driver(opts.device_id, opts.exposure_time, opts.save_jpeg, opts.roi, opts.no_save)
    d.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exposure_time", type=int, default=10000)
    parser.add_argument("-j", "--save-jpeg", action="store_true")
    parser.add_argument("-r", "--roi")
    parser.add_argument("-i", "--device-id")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args))
