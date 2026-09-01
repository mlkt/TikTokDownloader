from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter
from asyncio import CancelledError, run
from typing import Sequence


def parse_non_negative_integer(value: str) -> int:
    try:
        value = int(value)
    except ValueError:
        raise ArgumentTypeError(f"非负整数无效: {value}")
    if value < 0:
        raise ArgumentTypeError(f"非负整数无效: {value}")
    return value


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="DouK-Downloader",
        description=(
            "DouK-Downloader 命令行启动参数。\n"
            "不传任何参数时将启动交互式主菜单；传入参数将覆盖本次运行的部分设置。"
        ),
        add_help=False,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python main.py --help\n"
            "  DouK-Downloader --help\n"
            "  DouK-Downloader --suspend-batches 10 --suspend-interval 300\n"
            "完整参数说明请查阅项目文档。"
        ),
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="显示本帮助信息并退出。",
    )
    parser.add_argument(
        "--suspend-batches",
        type=parse_non_negative_integer,
        metavar="N",
        default=1,
        help=(
            "批量处理账号/合集时，每处理 N 个数据后暂停。"
            "N 必须为非负整数，0 表示禁用暂停。"
            "默认：1。"
        ),
    )
    parser.add_argument(
        "--suspend-interval",
        type=parse_non_negative_integer,
        metavar="N",
        default=30,
        help=(
            "每次暂停的时间，单位秒。"
            "N 必须为非负整数，0 表示禁用暂停。"
            "默认：30。"
        ),
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None):
    parser = create_parser()
    args, _ = parser.parse_known_args(argv)
    return args


async def main():
    args = parse_arguments()

    # 延迟导入，确保 --help 无需加载第三方依赖即可使用。
    from src.application import TikTokDownloader

    async with TikTokDownloader(
        suspend_batches=args.suspend_batches,
        suspend_interval=args.suspend_interval,
    ) as downloader:
        try:
            await downloader.run()
        except (
                KeyboardInterrupt,
                CancelledError,
        ):
            return


if __name__ == "__main__":
    run(main())
