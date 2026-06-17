# 小红书公开商品卡片监控系统

这个项目用于从用户自己能够正常打开的小红书公开笔记页面中读取公开展示的商品卡片信息，并生成 CSV 历史数据与 GitHub Pages 静态看板。

第一版只实现 `notes.txt` 链接列表采集。`keywords.txt` 已预留，后续再做关键词搜索。

## 采集字段

- `product_name`：商品名称
- `price`：商品价格
- `sold_count`：已售数量
- `note_url`：笔记链接
- `author_name`：作者昵称
- `captured_at`：抓取时间
- `source_type`：来源类型，第一版固定为 `note`

## 合规说明

本项目只读取公开笔记页面中已经展示给当前用户的可见文本，不破解接口，不逆向 App，不绕过登录，不绕过验证码，不使用代理池，不批量注册账号，不采集非公开后台数据或用户隐私数据。

如果页面出现验证码、安全验证、登录失效或访问异常，程序会停止采集，并提示用户手动处理。

## 目录结构

```text
xhs-product-monitor/
├── README.md
├── requirements.txt
├── .env.example
├── notes.txt
├── keywords.txt
├── src/
│   ├── main.py
│   ├── crawler.py
│   ├── parser.py
│   ├── storage.py
│   ├── exporter.py
│   └── config.py
├── data/
│   ├── products.csv
│   └── raw/
├── docs/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── data/
│       └── products.json
└── scripts/
    ├── install.sh
    ├── run.sh
    └── setup_cron.sh
```

## 准备 Ubuntu 服务器

可以购买任意云厂商的小型 Ubuntu 服务器，建议配置：

- Ubuntu 22.04 或 24.04
- 1 核 CPU / 1GB 内存起步
- 10GB 以上磁盘
- 能够通过 SSH 登录

登录服务器后先安装基础依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git cron
```

如果需要首次手动登录小红书，服务器还需要图形环境或浏览器可视化能力。更简单的方式是在带桌面的机器上先运行一次有头浏览器完成登录，然后把 `.browser_profile` 目录安全地迁移到服务器。

## 安装项目依赖

克隆仓库后进入项目目录：

```bash
git clone <你的仓库地址> xhs-product-monitor
cd xhs-product-monitor
bash scripts/install.sh
```

脚本会完成：

- 创建 `.venv`
- 安装 Python 依赖
- 安装 Playwright Chromium
- 如果没有 `.env`，从 `.env.example` 复制一份

如需手动安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

## 配置环境变量

编辑 `.env`：

```text
HEADLESS=false
USER_DATA_DIR=.browser_profile
NOTES_FILE=notes.txt
CSV_PATH=data/products.csv
JSON_PATH=docs/data/products.json
MAX_NOTES_PER_RUN=100
WAIT_SECONDS=5
```

说明：

- `HEADLESS=false`：有头浏览器，适合首次手动登录。
- `HEADLESS=true`：无头模式，适合服务器定时运行。
- `USER_DATA_DIR`：浏览器登录状态保存目录。
- `MAX_NOTES_PER_RUN`：单次最多采集多少个笔记链接。
- `WAIT_SECONDS`：页面等待商品卡片出现的时间。

## 首次手动登录小红书

首次运行建议保持：

```text
HEADLESS=false
```

然后执行：

```bash
source .venv/bin/activate
python src/main.py
```

浏览器打开后，按正常方式手动登录小红书。如果遇到验证码，请人工完成。程序不会绕过验证码。

登录状态会保存在 `.browser_profile`。之后可以把 `.env` 改成：

```text
HEADLESS=true
```

再用于服务器定时运行。

## 填写 notes.txt

每行一个公开笔记链接：

```text
https://www.xiaohongshu.com/explore/xxxxxxxx
https://www.xiaohongshu.com/explore/yyyyyyyy
```

空行和以 `#` 开头的注释行会被忽略。

## 手动运行

```bash
bash scripts/run.sh
```

脚本会执行：

```bash
python src/main.py
git add data/products.csv docs/data/products.json
git commit -m "update product data"
git push
```

如果没有数据变化，脚本会输出 `数据没有变化，跳过 commit。` 并正常退出。

## 数据保存与排序

程序会保存两个文件：

- `data/products.csv`：历史留存数据
- `docs/data/products.json`：GitHub Pages 看板读取的数据

去重规则：

```text
note_url + product_name
```

同一个商品多次抓取时，保留 `captured_at` 最新的记录。

导出的 JSON 默认按 `sold_count` 从高到低排序，并保留 Top1000。

## 设置 cron 定时运行

每天上午 9 点运行的 cron 示例：

```text
0 9 * * * cd /opt/xhs-product-monitor && bash scripts/run.sh
```

如果项目部署在当前目录，可以直接执行：

```bash
bash scripts/setup_cron.sh
```

日志会写入：

```text
logs/cron.log
```

## 开启 GitHub Pages

1. 推送代码到 GitHub 仓库。
2. 打开仓库的 Settings。
3. 进入 Pages。
4. Source 选择 `Deploy from a branch`。
5. Branch 选择主分支，目录选择 `/docs`。
6. 保存后等待 GitHub Pages 发布。

发布完成后，打开 Pages 地址即可看到数据看板。

## 前端看板功能

`docs/index.html` 会读取 `docs/data/products.json`，支持：

- 表格展示商品名、价格、已售数量、作者、笔记链接、抓取时间
- 按销量排序
- 按价格排序
- 商品名搜索
- 默认展示前 1000 条
- 点击笔记链接打开原笔记

## 常见异常

- 页面打不开：检查网络、链接是否有效。
- 商品卡片不存在：程序会跳过该笔记并记录日志。
- 价格解析失败：价格字段会为空，但记录仍可保留。
- 销量解析失败：销量字段会为空，并排在末尾。
- 登录失效：使用 `HEADLESS=false` 重新手动登录。
- 验证码出现：程序停止，请手动处理后再运行。
- 网络超时：检查服务器网络，稍后重试。
- Git 没有变化无法 commit：`scripts/run.sh` 已处理，不会报错。

## 关键词搜索

`keywords.txt` 已预留。第一版不主动搜索关键词，建议先用明确的公开笔记链接跑通采集、保存和看板发布流程。
