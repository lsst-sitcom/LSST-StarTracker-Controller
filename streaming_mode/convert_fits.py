import argparse
import asyncio
import pathlib

from astropy.io import fits
import matplotlib.pyplot as pl
import matplotlib.cm as cm
import numpy as np

def save_files(file_list: list) -> None:
    output_dir = pathlib.Path("~/converted").expanduser()
    for input_file in file_list:
        image_data = fits.getdata(input_file, ext=1)
        name = input_file.with_suffix(".png").name
        med = np.median(image_data)
        fig = pl.figure()
        pl.imshow(image_data, cmap=cm.Greys_r, vmin=med-0.2*med, vmax=med+0.2*med)
        fig.savefig(output_dir / name, dpi=fig.dpi)
        pl.close()

async def main(opts: argparse.Namespace) -> None:
    input_file_list = list(opts.data_dir.iterdir())
    num_procs = 6
    block_size = len(input_file_list) // num_procs
    tasks = []
    for i in range(num_procs):
        block = input_file_list[i * block_size: (i + 1) * block_size]
        tasks.append(asyncio.to_thread(save_files(block)))
    block = input_file_list[(i + 1) * block_size:]
    tasks.append(asyncio.to_thread(save_files(block)))
    _ = await asyncio.gather(*tasks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=pathlib.Path)
    args = parser.parse_args()
    asyncio.run(main(args))
