from pathlib import Path


def rename(loc):
    old = input('Enter the old name: ')
    new = input('Enter the new name:')
    failed = []
    for f in loc.iterdir():
        if f.is_file():
            name = f.stem
            ext = f.suffix
            if name == old:
                target = loc / f'{new}{ext}'
                try:
                    f.rename(target)
                except PermissionError:
                    failed.append(name)

    return(failed)


def remove(loc):
    chars = input('Enter the characters to remove: ')
    ext_in = input('Enter the filetype(s) (blank for all, comma separated): ')
    ext_list = [f'.{val.strip().lower()}' for val in ext_in.split(',')]
    failed = []
    for f in loc.iterdir():
        if f.is_file():
            name = f.stem
            ext = f.suffix.lower()
            target = loc / f'{name.replace(chars, "")}{ext}'
            if ext in ext_list or not ext_list:
                try:
                    f.rename(target)
                except PermissionError:
                    failed.append(name)

    return failed


if __name__ == "__main__":
    opts = [rename, remove]
    for i, opt in enumerate(opts):
        print(f'{i}: {opt.__name__}')
    val = int(input('Select a function: '))
    loc = Path(input('Enter the directory path: '))

    fn = opts[val]
    errors = fn(loc)
    [print(fail) for fail in errors]
