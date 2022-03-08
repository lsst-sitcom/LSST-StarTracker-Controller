import argparse
import os
from time import sleep
import tkinter as tk
from typing import Optional
import shutil
import statistics as st
import subprocess
import sys

from astropy.io import fits
import cv2
import numpy as np
from pymba import Vimba, Frame

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", help="Use debugging camera config")
parser.add_argument("--output-dir", default=os.path.expanduser("~/Desktop"),
                    help="Change the default output directory.")
args = parser.parse_args()

RESULTS_DIR = "results"
ROI_SIZE = 30

if args.debug:
    PIXEL_FORMAT = "Mono8"
    PIXEL_DTYPE = np.uint8
    PIXEL_SCALING = 75
else:
    PIXEL_FORMAT = "Mono14"
    PIXEL_DTYPE = np.uint16
    PIXEL_SCALING = 4000

global image
global scaled_image


def display_frame(frame: Frame, delay: Optional[int] = 1) -> None:

    # get a copy of the frame data
    global image
    image = get_frame_array(frame)

    # display image
    cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Image', 600, 600)
    cv2.imshow('Image', image)
    cv2.setMouseCallback('Image', display_zoom)
    cv2.createTrackbar('Scaling', 'Image', 0, PIXEL_SCALING, image_scaling)
    cv2.waitKey(delay)

def display_zoom(event, x: int, y:int, flags: dict, param) -> None:
    if event == cv2.EVENT_MOUSEMOVE:
        global scaled_image
        global image
        y_max, x_max = image.shape
        y_lower = y - ROI_SIZE
        y_upper = y + ROI_SIZE
        x_lower = x - ROI_SIZE
        x_upper = x + ROI_SIZE
        if y_upper >= y_max:
            y_upper = y_max
            y_lower = y_upper - 2 * ROI_SIZE
        if x_upper >= x_max:
            x_upper = x_max
            x_lower = x_upper - 2 * ROI_SIZE
        if y_lower <= 0:
            y_lower = 0
            y_upper = y_lower + 2 * ROI_SIZE
        if x_lower <= 0:
            x_lower = 0
            x_upper = x_lower + 2 * ROI_SIZE
        #print(x, x_lower, x_upper, y, y_lower, y_upper)
        try:
            img_zoom = scaled_image[y_lower:y_upper,x_lower:x_upper]
        except NameError:
            img_zoom = image[y_lower:y_upper,x_lower:x_upper]

        cv2.namedWindow('Zoom', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Zoom', 200, 200)
        cv2.imshow('Zoom', img_zoom)

def image_scaling(pos: int):
    global scaled_image
    global image

    scaled_image = cv2.convertScaleAbs(image, alpha=1, beta=pos)
    cv2.imshow('Image', scaled_image)
    cv2.waitKey(1)

def execute_exposure():
    cv2.destroyWindow('Zoom')
    global exposure_count

    list_RA = []
    list_DEC = []

    exp = float(exposure.get())
    num = int(number.get())
    sol = s.get()
    res = r.get()

    if res == 1:
        f = open(os.path.join(args.output_dir, RESULTS_DIR, 'results.csv'), 'w')

    camera.stop_frame_acquisition()
    camera.disarm()
    camera.arm('SingleFrame')
    camera.ExposureAuto = 'Off'
    camera.ExposureTimeAbs = exp * (10 ** 6)

    for i in range(num):
        frame = camera.acquire_frame(int(2.5e+7))
        image = get_frame_array(frame)
        hdu = fits.PrimaryHDU(image)
        hdu.writeto(os.path.join(args.output_dir, RESULTS_DIR, 'exposure_') + str(i + exposure_count) + '.fits')
        cv2.imwrite(os.path.join(args.output_dir, RESULTS_DIR, 'exposure_') + str(i + exposure_count) + '.jpeg',
                    image)

        if sol == 0:
            cmd = ['solve-field', '--use-sextractor', '--guess-scale', '--cpulimit', '10',
                   os.path.join(args.output_dir, RESULTS_DIR, 'exposure_') + str(i + exposure_count) + '.fits']
            result = subprocess.check_output(cmd, cwd=os.path.join(args.output_dir, RESULTS_DIR))

            if b'Total CPU time limit reached' in result or \
               b'Did not solve (or no WCS file was written)' in result:
                display.insert(tk.END, 'Exposure ' + str(i + exposure_count) + ': Unable to solve \n')
                display.update()

                if res == 1:
                    f.write('Exposure ' + str(i + exposure_count) + ': Unable to solve \n')

            else:
                guide_front = result.index(b'Field center: (RA,Dec) = ') + \
                    len('Field center: (RA,Dec) = ')
                guide_back = result.index(b'Field center: (RA H:M:S, Dec D:M:S) =')

                point = result[guide_front:guide_back - 6].decode()

                display.insert(tk.END, 'Exposure ' + str(i + exposure_count) + ': ' + point + '\n')
                display.update()

                if res == 1:
                    f.write('Exposure ' + str(i + exposure_count) + ': ' + point + '\n')

                RA = float(point[point.index('(') + 1:point.index(',')])
                DEC = float(point[point.index(',') + 2:point.index(')')])

                list_RA.append(RA)
                list_DEC.append(DEC)

    exposure_count += (i + 1)

    if res == 1 and list_RA != []:
        f.write('\n')
        f.write('Mean RA: ' + str(st.mean(list_RA)))
        f.write('   RA std: ' + str(st.stdev(list_RA)) + '\n')
        f.write('Mean DEC: ' + str(st.mean(list_DEC)))
        f.write('   DEC std: ' + str(st.stdev(list_DEC)) + '\n\n')

    if res == 1:
        f.close()

    camera.ExposureTimeAbs = 1e+3
    camera.disarm()
    camera.arm('Continuous', display_frame)
    camera.ExposureAuto = 'Continuous'
    camera.start_frame_acquisition()

    sleep(1)

    win.mainloop()

def get_frame_array(frame: Frame) -> np.ndarray:
    return np.ndarray(buffer=frame.buffer_data(),
                      dtype=PIXEL_DTYPE,
                      shape=(frame.data.height, frame.data.width))

# ================= Setting up GUI ================= #
win = tk.Tk()
win.title('StarTracker Controller')
# win.geometry('600x400')

welcome = tk.Label(win, text='Welcome to the LSST StarTracker Controller!').grid(row=0, column=0, sticky='w')

space = tk.Label(win, text=' ').grid(row=1, column=0)

exposure_label = tk.Label(win, text='Exposure time in seconds:').grid(row=2, column=0)
exposure = tk.Entry(win)
exposure.grid(row=2, column=1, sticky='w')
exposure.insert(tk.END, '15')

number_label = tk.Label(win, text='Number of exposures taken:').grid(row=3, column=0)
number = tk.Entry(win)
number.grid(row=3, column=1, sticky='w')
number.insert(tk.END, '1')

solve_label = tk.Label(win, text='Disable Astrometry.net solutions:').grid(row=4, column=0)
s = tk.IntVar()
solve = tk.Checkbutton(win, variable=s)
solve.grid(row=4, column=1, stick='w')

solve_label = tk.Label(win, text='Export Astrometry.net solutions to a CSV file:').grid(row=5, column=0)
r = tk.IntVar()
results = tk.Checkbutton(win, variable=r)
results.grid(row=5, column=1, stick='w')


space2 = tk.Label(win, text=' ').grid(row=6, column=0)
space3 = tk.Label(win, text='  Results:').grid(row=7, column=0, stick='w')

display = tk.Text(master=win, height=15, width=50)
display.grid(row=8, column=0)

start = tk.Button(win, text='Start Exposure', command=execute_exposure).grid(row=9, column=2, stick='E')

# ================================================== #

cv2.destroyAllWindows()
os.chdir(args.output_dir)
results_path = os.path.join(os.curdir, RESULTS_DIR)
if os.path.exists(results_path):
    shutil.rmtree(os.path.join(os.curdir, RESULTS_DIR))
os.makedirs(RESULTS_DIR)

global exposure_count
exposure_count = 0

with Vimba() as vimba:
    camera = vimba.camera(0)
    camera.open()

    # arm the camera and provide a function to be called upon frame ready
    camera.PixelFormat = PIXEL_FORMAT
    camera.arm('Continuous', display_frame)
    camera.ExposureTimeAbs = 1e+3
    camera.ExposureAuto = 'Continuous'
    camera.start_frame_acquisition()

    sleep(1)

    win.mainloop()

    cv2.destroyAllWindows()
    camera.stop_frame_acquisition()
    camera.disarm()
    camera.close()
    sys.exit()

    del exposure_count
