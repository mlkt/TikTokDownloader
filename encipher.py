from __future__ import annotations

import json
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

from javascript import require

from src.custom import USERAGENT
from src.encrypt.aBogus import ABogus


__all__ = [
    "DouYinParams"
]


ROOT = Path(__file__).resolve().parent
WEB_SIGN_DIR = ROOT / "douyin_websign"


def _find_js(filename: str) -> Path:
    """
    兼容两种目录结构：

    douyin_websign/
        xxx.js

    或：

    douyin_websign/
        vendor/
            xxx.js
    """

    path = WEB_SIGN_DIR / filename

    if path.is_file():
        return path

    path = WEB_SIGN_DIR / "vendor" / filename

    if path.is_file():
        return path

    raise FileNotFoundError(
        f"找不到 Douyin WebSign 文件: {filename}\n"
        f"搜索目录: {WEB_SIGN_DIR}"
    )


ENVIRONMENT_JS = _find_js(
    "environment.js"
)

RUNTIME_JS = _find_js(
    "runtime_bundler_34.js"
)

WEBMSSDK_JS = _find_js(
    "webmssdk.es5.js"
)

SDK_GLUE_JS = _find_js(
    "sdk-glue.js"
)


# ============================================================
# 工具
# ============================================================


def _query_to_string(
    query: dict | str | None,
) -> str:

    if query is None:
        return ""

    if isinstance(query, str):
        return query

    if isinstance(query, dict):
        return urlencode(
            query,
            doseq=True,
            safe="=",
        )

    raise TypeError(
        f"query 类型错误: {type(query)!r}"
    )


def _get_query_value(
    query: str,
    name: str,
) -> str:

    for key, value in parse_qsl(
        query,
        keep_blank_values=True,
    ):
        if key == name:
            return value

    return ""


# ============================================================
# Douyin WebSign
# ============================================================


class _DouyinWebSign:
    """
    使用 JSPyBridge 执行抖音 WebSecSDK。

    JS：

        environment.js
        runtime_bundler_34.js
        webmssdk.es5.js
        sdk-glue.js

    初始化：

        window._SdkGlueInit(...)

    签名：

        window.use("webSignUrl")
    """

    def __init__(self):
        self._module = None
        self._bridge_file: Path | None = None

        self._check_files()

    @staticmethod
    def _check_files():

        files = (
            ENVIRONMENT_JS,
            RUNTIME_JS,
            WEBMSSDK_JS,
            SDK_GLUE_JS,
        )

        missing = [
            str(path)
            for path in files
            if not path.is_file()
        ]

        if missing:
            raise FileNotFoundError(
                "Douyin WebSign JS 文件缺失:\n"
                + "\n".join(missing)
            )

    def _create_bridge(self) -> Path:

        if self._bridge_file is not None:
            return self._bridge_file

        source = f"""
const fs = require("fs");
const vm = require("vm");

const context = vm.createContext({{
    console,
    Buffer,
    URL,
    URLSearchParams,
    TextEncoder,
    TextDecoder,

    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,

    navigator: {{
        userAgent:
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
            "AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/150.0.0.0 Safari/537.36",

        language: "zh-CN",
        platform: "Win32"
    }},

    location: {{
        href: "https://www.douyin.com/"
    }}
}});

context.globalThis = context;
context.window = context;
context.self = context;
context.global = context;

context.atob = function(value) {{
    return Buffer
        .from(String(value), "base64")
        .toString("utf8");
}};

context.btoa = function(value) {{
    return Buffer
        .from(String(value), "utf8")
        .toString("base64");
}};

context.__unixMillis = function() {{
    return Date.now();
}};

const files = [
    {json.dumps(str(ENVIRONMENT_JS.resolve()))},
    {json.dumps(str(RUNTIME_JS.resolve()))},
    {json.dumps(str(WEBMSSDK_JS.resolve()))},
    {json.dumps(str(SDK_GLUE_JS.resolve()))}
];

for (const file of files) {{
    const code = fs.readFileSync(
        file,
        "utf8"
    );

    vm.runInContext(
        code,
        context,
        {{
            filename: file
        }}
    );
}}


// 与 videodown 的 SDK 初始化保持一致
vm.runInContext(
`
window._SdkGlueInit(
    {{
        self: {{
            aid: 6383,
            pageId: 6241
        }},

        bdms: {{
            aid: 6383,
            pageId: 6241,
            paths: [
                "^/aweme/v1/",
                "^/aweme/v2/"
            ],
            boe: false,
            ddrt: 8.5,
            ic: 8.5
        }}
    }},
    {{}}
);
`,
    context
);


module.exports = {{

    sign: function(targetURL, uifid) {{

        context.__uifid = String(uifid);

        const fn =
            vm.runInContext(
                `window.use("webSignUrl")`,
                context
            );

        if (typeof fn !== "function") {{
            throw new Error(
                "window.use('webSignUrl') 没有返回函数"
            );
        }}

        const result =
            fn(String(targetURL));

        if (!result) {{
            throw new Error(
                "webSignUrl 返回为空"
            );
        }}

        const url =
            result.url || "";

        const headers =
            result.headers || {{}};

        const signature =
            headers[
                "x-secsdk-web-signature"
            ] || "";

        if (!url) {{
            throw new Error(
                "webSignUrl 没有返回 URL"
            );
        }}

        if (!signature) {{
            throw new Error(
                "webSignUrl 没有返回 " +
                "x-secsdk-web-signature"
            );
        }}

        return JSON.stringify({{
            url,
            signature
        }});
    }}
}};
"""

        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".cjs",
            prefix="douyin_websign_",
            delete=False,
            encoding="utf-8",
        )

        try:

            tmp.write(source)
            tmp.close()

            self._bridge_file = Path(
                tmp.name
            )

            return self._bridge_file

        except Exception:

            try:
                Path(tmp.name).unlink(
                    missing_ok=True
                )
            except Exception:
                pass

            raise

    def sign(
        self,
        url: str,
        uifid: str,
    ) -> tuple[str, str]:

        bridge = self._create_bridge()

        if self._module is None:
            self._module = require(
                str(bridge.resolve())
            )

        result = self._module.sign(
            url,
            uifid,
        )

        if isinstance(result, str):
            result = json.loads(result)

        else:
            try:
                result = dict(result)

            except Exception as exc:

                raise RuntimeError(
                    "无法解析 Douyin WebSign 返回值: "
                    f"{result!r}"
                ) from exc

        signed_url = result.get(
            "url"
        )

        signature = result.get(
            "signature"
        )

        if not signed_url:
            raise RuntimeError(
                "Douyin WebSign 返回 URL 为空"
            )

        if not signature:
            raise RuntimeError(
                "Douyin WebSign 返回签名为空"
            )

        return (
            str(signed_url),
            str(signature),
        )


# ============================================================
# DouYinParams
# ============================================================


class DouYinParams:
    """
    TikTokDownloader 外部抖音参数实现。

    sign():

        只计算 a_bogus

    sign_url():

        a_bogus
            ↓
        完整 URL
            ↓
        x-secsdk-web-signature
            ↓
        返回最终 query
    """

    def __init__(self):

        self._abogus = ABogus()

        self._websign = (
            _DouyinWebSign()
        )

    # --------------------------------------------------------
    # ABogus
    # --------------------------------------------------------

    def _get_a_bogus(
        self,
        query: str,
        data: dict | str | None,
        method: str,
        user_agent: str,
    ) -> str:

        # 注意：
        # 当前 TikTokDownloader ABogus.get_value()
        # 不能使用 query= 关键字参数。
        return self._abogus.get_value(
            query,
            data,
            method,
            user_agent=user_agent,
        )

    # --------------------------------------------------------
    # sign
    # --------------------------------------------------------

    def sign(
        self,
        query: dict | str = "",
        data: dict | str | None = None,
        method: str = "",
        user_agent: str = USERAGENT,
        ms_token: str = "",
    ) -> dict[str, str]:

        query = _query_to_string(
            query
        )

        if not method:
            method = "GET"

        if not user_agent:
            user_agent = USERAGENT

        a_bogus = self._get_a_bogus(
            query,
            data,
            method,
            user_agent,
        )

        return {
            "a_bogus": a_bogus
        }

    # --------------------------------------------------------
    # sign_url
    # --------------------------------------------------------

    def sign_url(
        self,
        base_url: str = "",
        query: dict | str = "",
        data: dict | str | None = None,
        method: str = "",
        user_agent: str = USERAGENT,
        ms_token: str = "",
    ) -> str:

        query = _query_to_string(
            query
        )

        if not method:
            method = "GET"

        if not user_agent:
            user_agent = USERAGENT

        # ================================================
        # 1. a_bogus
        # ================================================

        a_bogus = self._get_a_bogus(
            query,
            data,
            method,
            user_agent,
        )

        # 删除旧 a_bogus
        query_items = [
            (key, value)
            for key, value in parse_qsl(
                query,
                keep_blank_values=True,
            )
            if key != "a_bogus"
        ]

        query_items.append(
            (
                "a_bogus",
                a_bogus,
            )
        )

        signed_query = urlencode(
            query_items,
            doseq=True,
        )

        # ================================================
        # 2. 没有 URL
        # ================================================

        if not base_url:

            return signed_query

        # ================================================
        # 3. UIFID
        # ================================================

        uifid = _get_query_value(
            signed_query,
            "uifid",
        )

        # 不是所有抖音接口都需要 WebSign。
        # 没有 UIFID 时保持正常 a_bogus 行为。
        if not uifid:

            separator = (
                "&"
                if "?" in base_url
                else "?"
            )

            return (
                f"{base_url}"
                f"{separator}"
                f"{signed_query}"
            )

        # ================================================
        # 4. 完整 URL
        # ================================================

        parts = urlsplit(
            base_url
        )

        existing_query = (
            parts.query
        )

        if existing_query:

            full_query = (
                existing_query
                + "&"
                + signed_query
            )

        else:

            full_query = signed_query

        full_url = (
            base_url.split("?")[0]
            + "?"
            + full_query
        )

        # ================================================
        # 5. WebSign
        # ================================================

        signed_url, signature = (
            self._websign.sign(
                full_url,
                uifid,
            )
        )

        # ================================================
        # 6. WebSign 返回完整 URL
        #
        # TikTokDownloader 后续会：
        #
        #     url + "?" + params
        #
        # 所以拆出 query 返回即可。
        # ================================================

        final_query = urlsplit(
            signed_url
        ).query

        if not final_query:

            raise RuntimeError(
                "Douyin WebSign 返回 URL "
                "没有 query 参数"
            )

        # 某些 SDK 版本会把签名放在
        # headers 而不是返回 URL 的 query。
        if (
            "x-secsdk-web-signature="
            not in final_query
        ):

            final_query += (
                "&x-secsdk-web-signature="
                + signature
            )

        return final_query

