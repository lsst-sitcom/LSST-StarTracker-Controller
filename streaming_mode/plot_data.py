import argparse
import pathlib

from astropy.io import fits
from astropy.visualization import astropy_mpl_style
import matplotlib
import matplotlib.pyplot as plt
plt.style.use(astropy_mpl_style)
matplotlib.use('QtAgg')


def main(opts: argparse.Namespace) -> None:
    input_file = pathlib.Path(opts.data_file).expanduser()
    image_data = fits.getdata(input_file, ext=1)
    print(image_data.shape)

    plt.figure()
    plt.imshow(image_data, cmap='gray')
    plt.colorbar()
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file")
    args = parser.parse_args()
    main(args)
