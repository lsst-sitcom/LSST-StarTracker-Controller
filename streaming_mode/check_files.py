import argparse
import pathlib

def main(opts: argparse.Namespace) -> None:
    data_dir = pathlib.Path("~/data").expanduser()
    files = sorted(list(data_dir.iterdir()))
    last_file = files[-1].stem
    suffix = files[-1].suffix
    print(last_file)
    last_index = last_file.split("_")[-1]
    for i in range(1, int(last_index)):
        new_stem = last_file.replace(last_index, f"{i:07d}")
        new_file = data_dir / f"{new_stem}{suffix}"
        if not new_file.exists():
            print(f"{new_file.name} does not exist")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
