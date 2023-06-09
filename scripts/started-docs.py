from character.lib import log
from modules import script_callbacks
from fastapi import FastAPI
import gradio as gr

description = """

## 角色形象组件 

### 签名说明

- 签名算法: SHA256
- 签名数据: POST_RAW + HEAD(X-Signature-Time)
- 参数 - X-Signature-Name: 调用方名称对应密钥，每个调用方需要提供公钥（2048+）
- 参数 - X-Signature-Time: 签名时间戳，有效期60秒
- 参数 - X-Signature: 签名内容，base64
- 请求数据包: 仅支持json

> 样例代码

```php
$signatureName = 'my';
$privateKeyPath = "./x/{$signatureName}-private.pem"
$signatureTime = time();
$data = ['user_name' => 'test'];
$json = json_encode($data);
$source = $json . $signatureTime;
$privateKey = openssl_pkey_get_private(file_get_contents($privateKeyPath));
openssl_sign($source, $signature, $privateKey, OPENSSL_ALGO_SHA256);
```

> 样例请求

```bash
curl -XGET 'http://host/character/v1/status' \\
    --silent \\
    -H 'Accept: application/json' \\
    -H 'Content-Type: application/json' \\
    -H 'X-Signature-Name:my' \\
    -H 'X-Signature-Time:1681124800' \\
    -H 'X-Signature:Mb0GO2PcPNLO42ZNLZEaqU92+...fCIx+wig=' \\
    -d ''
```

"""


def update_tags(_: gr.Blocks, app: FastAPI):
    if not app.openapi_tags:
        app.openapi_tags = []

    app.openapi_tags.append({
        "name": "Character",
        "description": "角色形象"
    })

    app.openapi_tags.append({
        "name": "Status",
        "description": "系统状态"
    })

    app.description = app.description + description

    log("Tags loaded")

script_callbacks.on_app_started(update_tags)


