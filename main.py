from asyncio import CancelledError, run

from src.cli_edition import load_arguments


async def main():
    load_arguments()

    # 延迟导入，确保 --help 无需加载第三方依赖即可使用。
    from src.application import TikTokDownloader

    async with TikTokDownloader() as downloader:
        try:
            await downloader.run()
        except (
                KeyboardInterrupt,
                CancelledError,
        ):
            return


if __name__ == "__main__":
    run(main())
