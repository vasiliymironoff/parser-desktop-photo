from loaders import SyncLoaderPhoto, AsyncLoaderPhoto
from argparse import ArgumentParser


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-s', '--synchronously', action='store_true', help='Использовать синхронное скачивание (по умолчанию асинхронное)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Подробная информация о загрузке')
    args = parser.parse_args()
    if args.synchronously:
        lp = SyncLoaderPhoto(args.verbose)
        lp.run()
    else:
        lp = AsyncLoaderPhoto(args.verbose)
        lp.run()
