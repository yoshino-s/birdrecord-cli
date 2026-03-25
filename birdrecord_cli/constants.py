"""HTTP/crypto defaults and static configuration."""

AES_KEY = b"3583ec0257e2f4c8195eec7410ff1619"
AES_IV = b"d93c0d5ec6352f20"

BASE_URL = "https://weixin.birdrecord.cn"

# Default taxon/search version from captured traffic.
DEFAULT_TAXON_VERSION = "Z4-67FA07177A544FBD96006A7CC7489D25"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 "
    "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Mac "
    "MacWechat/WMPF MacWechat/3.8.7(0x13080712) UnifiedPCMacWechat(0xf264181d) XWEB/19024"
)

DEFAULT_REFERER = "https://servicewechat.com/wx9ebf8f0d26aa0240/91/page-frame.html"
