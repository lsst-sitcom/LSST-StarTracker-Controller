import argparse
import pathlib

from astropy.io import fits
from astropy.visualization import astropy_mpl_style
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
plt.style.use(astropy_mpl_style)
matplotlib.use('QtAgg')


def print_min_max(data: np.ndarray) -> None:
    print(f"Max: {np.max(data)}")
    print(f"Min: {np.min(data)}")


def main(opts: argparse.Namespace) -> None:
    input_file = pathlib.Path(opts.data_file).expanduser()
    image_data = fits.getdata(input_file, ext=1)
    print(image_data.shape)
    print(f"{input_file.name}")
    print_min_max(image_data)

    if opts.diff:
        image_data = image_data.astype(np.int16)
        data_file = input_file.stem
        parts = str(data_file).split("_")
        seq_num = int(parts[-1])
        new_seq_num = seq_num + 10
        parts[-1] = f"{new_seq_num:07d}"
        new_input_file = input_file.parent / f"{'_'.join(parts)}{input_file.suffix}"
        new_image_data = fits.getdata(new_input_file, ext=1)
        print(f"{new_input_file.name}")
        print_min_max(new_image_data)
        new_image_data = new_image_data.astype(np.int16)
        image_data = image_data - new_image_data
        print("Diff Image:")
        print_min_max(image_data)

    plt.figure()
    plt.imshow(image_data, cmap='gray')
    plt.colorbar()
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file")
    parser.add_argument("--diff", action="store_true", help="Do diference image on subsequent frame")
    args = parser.parse_args()
    main(args)
