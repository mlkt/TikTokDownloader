from argparse import ArgumentParser, ArgumentTypeError
from asyncio import CancelledError, run

from src.application import TikTokDownloader


def parse_boolean(value: str) -> bool:
    if value.lower() in {"true", "1"}:
        return True
    if value.lower() in {"false", "0"}:
        return False
    raise ArgumentTypeError(f"布尔值无效: {value}")


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
