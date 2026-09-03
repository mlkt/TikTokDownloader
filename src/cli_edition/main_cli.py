from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter
from dataclasses import dataclass, fields
from typing import Sequence

__all__ = [
    "CliOptions",
    "CLI",
    "cli",
    "parse_arguments",
    "load_arguments",
    "reset_options",
]


@dataclass
class CliOptions:
    suspend_batches: int = 1
    suspend_interval: int = 30


CLI = CliOptions()


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


def parse_arguments(
    argv: Sequence[str] | None = None,
) -> CliOptions:
    parser = create_parser()
    args, _ = parser.parse_known_args(argv)
    return CliOptions(
        suspend_batches=args.suspend_batches,
        suspend_interval=args.suspend_interval,
    )


def load_arguments(
    argv: Sequence[str] | None = None,
) -> CliOptions:
    options = parse_arguments(argv)
    for field in fields(options):
        setattr(CLI, field.name, getattr(options, field.name))
    return CLI


def reset_options() -> CliOptions:
    for field in fields(CLI):
        setattr(CLI, field.name, field.default)
    return CLI


def cli(
    argv: Sequence[str] | None = None,
) -> CliOptions:
    return load_arguments(argv)
