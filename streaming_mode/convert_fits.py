import argparse
import pathlib

from astropy.io import fits
import matplotlib.pyplot as pl
import matplotlib.cm as cm
import numpy as np

OUTPUT_DIR = pathlib.Path("~/converted").expanduser()


def main(opts: argparse.Namespace) -> None:
    for input_file in opts.data_dir.iterdir():
        image_data = fits.getdata(input_file, ext=1)
        name = input_file.with_suffix(".png").name
        med = np.median(image_data)
        fig = pl.figure()
        pl.imshow(image_data, cmap=cm.Greys_r, vmin=med-0.2*med, vmax=med+0.2*med)
        fig.savefig(OUTPUT_DIR / name, dpi=fig.dpi)
        pl.close()

	
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=pathlib.Path)
    args = parser.parse_args()
    main(args)
