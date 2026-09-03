import sys
from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Sequence

__all__ = [
    "CliOptions",
    "CLI",
    "cli",
    "parse_arguments",
    "load_arguments",
    "reset_options",
    "ROOT",
    "resolve_volume_path",
]

ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent.parent.parent
)


def resolve_volume_path(value: str | Path | None = None) -> Path:
    if not value:
        return ROOT.joinpath("Volume")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd().joinpath(path)
    return path.resolve()


@dataclass
class CliOptions:
    volume: Path = ROOT.joinpath("Volume")
    original_quality_mode: str = "config"
    original_quality_value: bool | None = None
    record: bool | None = None
    suspend_batches: int = 1
    suspend_interval: int = 30


CLI = CliOptions()


def parse_boolean(value: str) -> bool:
    if value.lower() in {"true", "1"}:
        return True
    if value.lower() in {"false", "0"}:
        return False
    raise ArgumentTypeError(f"布尔值无效: {value}")


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
            "  DouK-Downloader --original-quality-mode global --original-quality true --record false\n"
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
        "--volume",
        type=str,
        metavar="PATH",
        default=None,
        help=(
            "指定 Volume 数据目录，包含配置文件、数据库、缓存和日志。"
            "相对路径以启动时的当前工作目录为基准；省略时使用程序文件目录下的 Volume。"
            "默认：程序文件目录/Volume。"
        ),
    )
    parser.add_argument(
        "--original-quality-mode",
        choices=("config", "global", "override"),
        default="config",
        help=(
            "original_quality 优先级模式。"
            "可选值：config（默认，使用配置文件和账号级设置）、"
            "global（使用命令行值覆盖全局配置，账号级设置仍优先）、"
            "override（强制覆盖包括账号级设置在内的全部配置）。"
            "默认：config。"
        ),
    )
    parser.add_argument(
        "--original-quality",
        type=parse_boolean,
        metavar="{true,false}",
        default=None,
        help=(
            "original_quality 目标值，仅在 global/override 模式下必填。"
            "可选值：true、false（兼容 1、0，不区分大小写）。"
            "true 表示优先下载原画/最高画质，false 表示不强制原画。"
            "默认：未设置。"
        ),
    )
    parser.add_argument(
        "--record",
        type=parse_boolean,
        metavar="{true,false}",
        default=None,
        help=(
            "本次运行是否启用作品下载记录。"
            "可选值：true、false（兼容 1、0，不区分大小写）。"
            "省略时使用配置文件 Record 设置；传入后本次运行期间主菜单中的"
            "“作品下载记录”不可切换。"
            "默认：未设置。"
        ),
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
    volume = resolve_volume_path(args.volume)
    if args.original_quality_mode == "config" and args.original_quality is not None:
        parser.error("--original-quality 只能在 global/override 模式下使用")
    if (
        args.original_quality_mode in {"global", "override"}
        and args.original_quality is None
    ):
        parser.error(
            "--original-quality-mode 为 global/override 时必须提供 --original-quality"
        )
    return CliOptions(
        volume=volume,
        original_quality_mode=args.original_quality_mode,
        original_quality_value=args.original_quality,
        record=args.record,
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
