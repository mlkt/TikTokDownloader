from argparse import ArgumentParser, ArgumentTypeError
from asyncio import CancelledError, run

from src.application import TikTokDownloader


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


def parse_arguments():
    parser = ArgumentParser(
        description="DouK-Downloader 命令行参数",
    )
    parser.add_argument(
        "--original-quality-mode",
        choices=("auto", "override", "force"),
        default="auto",
        help="original_quality 优先级模式，默认 auto",
    )
    parser.add_argument(
        "--original-quality",
        type=parse_boolean,
        default=None,
        help="original_quality 目标值，override/force 模式必填",
    )
    parser.add_argument(
        "--record",
        type=parse_boolean,
        default=None,
        help="是否启用作品下载记录，默认使用配置文件设置",
    )
    parser.add_argument(
        "--suspend-batches",
        type=parse_non_negative_integer,
        default=1,
        help="每处理多少条数据后暂停，0 表示禁用，默认 1",
    )
    parser.add_argument(
        "--suspend-interval",
        type=parse_non_negative_integer,
        default=30,
        help="暂停秒数，0 表示禁用，默认 30",
    )
    args, _ = parser.parse_known_args()
    if args.original_quality_mode == "auto" and args.original_quality is not None:
        parser.error("--original-quality 只能在 override/force 模式下使用")
    if (
        args.original_quality_mode in {"override", "force"}
        and args.original_quality is None
    ):
        parser.error(
            "--original-quality-mode 为 override/force 时必须提供 --original-quality"
        )
    return args


async def main():
    args = parse_arguments()
    async with TikTokDownloader(
        original_quality_mode=args.original_quality_mode,
        original_quality_value=args.original_quality,
        record=args.record,
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
