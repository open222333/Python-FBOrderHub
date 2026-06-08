# Python-FBOrderHub

Flask + Vue 3 訂單管理系統，整合 Facebook Graph API 自動發文功能。

- **後台管理 UI**（Vue 3 + Vite + Bootstrap 5，支援行動裝置）
- **顧客下單頁**（純 HTML，無需登入，掃碼即可點餐）
- **商品管理**：上下架、庫存、排程自動下架
- **Facebook 社團/粉專自動發文**：發文範本 + Graph API v18
- **訂單管理**：顧客下單 → 後台接單 → 更新狀態
- **JWT 認證** + **角色權限**（admin / operator / viewer）
- **Swagger UI**（flasgger）
- **Docker 部署**：nginx + Flask + MongoDB，一鍵啟動

測試環境：Python 3.11.2

---

## 目錄

- [專案結構](#專案結構)
- [快速開始](#快速開始)
- [Docker 部署](#docker-部署)
- [域名部署](#域名部署)
- [主機 nginx 部署](#主機-nginx-部署)
- [API 說明](#api-說明)
- [設定檔說明](#設定檔說明)
- [Facebook 整合說明](#facebook-整合說明)
- [排程器說明](#排程器說明)
- [注意事項](#注意事項)

---

## 專案結構

```
Python-FBOrderHub/
├── run.py                          # 啟動入口（自動產生 SECRET_KEY、建立預設 admin 帳號）
├── gunicorn.py                     # Gunicorn 設定（含 post_fork 排程啟動）
├── Dockerfile
├── docker-compose.yml.default
├── .env.default
│
├── app/                            # Flask 應用程式
│   ├── __init__.py                 # 初始化、Swagger / JWT 設定、藍圖註冊
│   ├── auth/view.py                # POST /auth/login → 回傳 JWT token
│   ├── user/view.py                # 使用者 CRUD（admin 限定）
│   ├── admin/view.py               # GET /admin/ → Vue 3 後台管理 UI
│   ├── log/view.py                 # GET /log/ → 操作紀錄
│   ├── product/view.py             # 商品 CRUD + 上下架切換
│   ├── fb/view.py                  # Facebook 發文 + 發文範本管理
│   ├── order/view.py               # 訂單管理（後台）+ 顧客下單（公開）
│   └── templates/
│       ├── admin/index.html        # Vue 3 後台 SPA
│       └── shop/index.html         # 顧客下單靜態頁
│
├── frontend/                       # Vue 3 + Vite 原始碼
│   ├── vite.config.js
│   ├── src/
│   └── dist/                       # build 產出（被 Flask 提供）
│
├── conf/
│   ├── nginx/                      # nginx 設定（Docker / 主機模式）
│   ├── config.py                   # ProductionConfig / DevelopmentConfig 等
│   ├── config.ini.default
│   └── flask.json.default
│
└── src/
    ├── __init__.py                 # 讀取全部設定參數
    ├── mongo.py                    # MongoDB singleton
    ├── permissions.py              # @require_role 裝飾器
    ├── scheduler.py                # 排程器（自動下架）
    └── models/
        ├── base.py                 # BaseModel（共用 _serialize）
        ├── user.py
        ├── log.py
        ├── product.py              # Product model（含批次查詢、原子庫存）
        ├── order.py                # Order model
        └── fb_template.py          # FBTemplate model
```

---

## 快速開始

### 1. 複製設定檔

```bash
cp conf/config.ini.default conf/config.ini
cp conf/flask.json.default conf/flask.json
```

> `conf/flask.json` 的 `SECRET_KEY` 留空即可，`run.py` 啟動時會自動產生並寫入。

### 2. 設定 MongoDB 與 Facebook

編輯 `conf/config.ini`：

```ini
[MONGO]
MONGO_URI=mongodb://localhost:27017
MONGO_DB=fb_order_hub

[FACEBOOK]
FB_ACCESS_TOKEN=你的長效 User Access Token 或 Page Token
FB_GROUP_ID=你的社團 ID（發文用）
```

### 3. 安裝套件並啟動

```bash
pip install -r requirements.txt
python run.py
```

首次啟動自動建立預設帳號 `admin / admin`，**請立即修改密碼**。

| 服務 | 網址 |
|---|---|
| 後台管理 | http://127.0.0.1:5000/admin/ |
| 顧客下單 | http://127.0.0.1:5000/shop/ |
| Swagger UI | http://127.0.0.1:5000/apidocs |

### 4. 前端開發模式

```bash
cd frontend
npm install
npm run dev       # Vite dev server（含 proxy，自動轉發 API 至 :5000）
```

前端 dev server：http://localhost:5173/

### 5. 建置前端

```bash
cd frontend
npm run build     # 產出至 frontend/dist/（Flask 直接提供）
```

---

## Docker 部署

### 1. 準備設定檔

```bash
cp docker-compose.yml.default docker-compose.yml
cp .env.default .env
cp conf/config.ini.default conf/config.ini
cp conf/flask.json.default conf/flask.json
```

### 2. 調整 config.ini

```ini
[MONGO]
MONGO_URI=mongodb://mongo:27017
MONGO_DB=fb_order_hub

[FACEBOOK]
FB_ACCESS_TOKEN=你的 Token
FB_GROUP_ID=你的社團 ID
```

### 3. 啟動

```bash
docker compose up -d --build
```

### 服務一覽

| 服務 | 映像 | 對外埠號 | 說明 |
|---|---|---|---|
| `nginx` | nginx:alpine | **80** | 反向代理 |
| `app` | 本地建置 | — | Flask + Gunicorn（僅 Docker 內部） |
| `mongo` | mongo:7 | — | MongoDB |

啟動後透過 nginx 存取：

| 服務 | 網址 |
|---|---|
| 後台管理 | http://localhost/admin/ |
| 顧客下單 | http://localhost/shop/ |
| Swagger UI | http://localhost/apidocs |

### 常用指令

```bash
docker compose ps
docker compose logs -f app
docker compose exec app bash
docker compose down
docker compose down -v          # 停止並清除資料（不可逆）
docker compose build --no-cache
```

---

## 域名部署

`.env` 的 `NGINX_MODE` 控制 nginx 模式：

| `NGINX_MODE` | 說明 |
|---|---|
| `http` | 純 HTTP（預設） |
| `cloudflare` | Cloudflare Origin CA SSL |

---

### 模式一：HTTP（預設）

```env
NGINX_MODE=http
DOMAIN=_
```

---

### 模式二：Cloudflare SSL

#### 1. DNS 設定

Cloudflare Dashboard → DNS → 新增 A Record，Proxy 開啟。

#### 2. 建立 Origin CA 憑證

Cloudflare Dashboard → **SSL/TLS → Origin Server → Create Certificate**

```bash
mkdir -p /etc/ssl/cloudflare
nano /etc/ssl/cloudflare/origin.pem   # Origin Certificate
nano /etc/ssl/cloudflare/origin.key   # Private Key
chmod 600 /etc/ssl/cloudflare/origin.key
```

#### 3. 更新 .env

```env
NGINX_MODE=cloudflare
DOMAIN=your.domain.com
CF_CERT_DIR=/etc/ssl/cloudflare
```

#### 4. 啟動

```bash
docker compose up -d
```

> SSL/TLS 模式設為 **Full (Strict)**。

---

## 主機 nginx 部署

適用主機已安裝 nginx（80/443 已被佔用）的情境：

```
使用者 → 主機 nginx:80/443 → 127.0.0.1:5000（Docker app 容器）→ MongoDB 容器
```

設定檔：

| 檔案 | 說明 |
|---|---|
| `conf/nginx/host/http.conf` | 純 HTTP |
| `conf/nginx/host/cloudflare.conf` | Cloudflare Origin CA |
| `conf/nginx/host/https-letsencrypt.conf` | Let's Encrypt |

---

### Step 1：docker-compose.yml 移除 nginx，暴露 app port

```yaml
  app:
    ports:
      - "127.0.0.1:5000:5000"
```

### Step 2：安裝 nginx

```bash
sudo apt update && sudo apt install -y nginx
sudo systemctl enable --now nginx
```

### Step 3：建立站台設定

```bash
# HTTP
sudo cp conf/nginx/host/http.conf /etc/nginx/sites-available/flask-app
sudo nano /etc/nginx/sites-available/flask-app   # 將 YOUR_DOMAIN 改為實際域名或 _

# Cloudflare SSL
sudo cp conf/nginx/host/cloudflare.conf /etc/nginx/sites-available/flask-app

# Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your.domain.com
sudo cp conf/nginx/host/https-letsencrypt.conf /etc/nginx/sites-available/flask-app
```

### Step 4：啟用並重載

```bash
sudo ln -sf /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/flask-app
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### Step 5：啟動容器

```bash
docker compose up -d --build app mongo
```

---

## API 說明

### 公開端點（無需登入）

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/` | 健康檢查 |
| POST | `/auth/login` | 登入，回傳 JWT token |
| GET | `/admin/` | Vue 3 後台管理 UI |
| GET | `/shop/` | 顧客下單頁 |
| GET | `/apidocs` | Swagger UI |
| GET | `/order/public/products` | 取得上架商品（顧客用） |
| POST | `/order/public/` | 顧客提交訂單 |

### 受保護端點（需 `Authorization: Bearer <token>`）

| 方法 | 路徑 | 所需角色 | 說明 |
|---|---|---|---|
| GET | `/user/` | admin | 列出使用者 |
| POST | `/user/` | admin | 新增使用者 |
| PUT | `/user/<id>` | admin | 更新密碼或角色 |
| DELETE | `/user/<id>` | admin | 刪除使用者 |
| GET | `/log/` | 已登入 | 操作紀錄 |
| GET | `/product/` | 已登入 | 列出商品 |
| POST | `/product/` | admin/operator | 新增商品 |
| PUT | `/product/<id>` | admin/operator | 更新商品 |
| PATCH | `/product/<id>/status` | admin/operator | 切換上下架 |
| DELETE | `/product/<id>` | admin | 刪除商品 |
| GET | `/fb/templates` | 已登入 | 列出發文範本 |
| POST | `/fb/templates` | admin/operator | 新增範本 |
| PUT | `/fb/templates/<id>` | admin/operator | 更新範本 |
| DELETE | `/fb/templates/<id>` | admin | 刪除範本 |
| POST | `/fb/post` | admin/operator | 發文至 Facebook |
| GET | `/order/` | 已登入 | 列出訂單 |
| GET | `/order/<id>` | 已登入 | 取得單一訂單 |
| PATCH | `/order/<id>/status` | admin/operator | 更新訂單狀態 |

### 登入取得 Token

```bash
# 本機開發
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
# {"success": true, "token": "<jwt>", "role": "admin"}

curl http://127.0.0.1:5000/product/ \
  -H "Authorization: Bearer <jwt>"

# Docker 部署（port 80，經 nginx）
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

---

## 設定檔說明

### conf/config.ini

| 區塊 | 參數 | 說明 | 預設值 |
|---|---|---|---|
| `[LOG]` | `LOG_DISABLE` | 關閉 log（1=關閉） | `False` |
| | `LOG_PATH` | log 目錄 | `logs` |
| | `LOG_LEVEL` | 等級 | `WARNING` |
| `[SETTING]` | `FLASK_JSON_PATH` | flask.json 路徑 | `conf/flask.json` |
| `[MONGO]` | `MONGO_URI` | MongoDB 連線 URI | `mongodb://localhost:27017` |
| | `MONGO_DB` | 資料庫名稱 | `fb_order_hub` |
| `[FACEBOOK]` | `FB_ACCESS_TOKEN` | Graph API Token | _(空)_ |
| | `FB_GROUP_ID` | 發文目標社團 ID | _(空)_ |

### conf/flask.json

```json
{ "SECRET_KEY": "" }
```

`SECRET_KEY` 留空時，`run.py` 啟動會自動產生並寫入。

### 環境變數

| 變數 | 說明 | 預設值 |
|---|---|---|
| `FLASK_PORT` | Flask 內部埠號 | `5000` |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | Token 有效時數 | `8` |

---

## Facebook 整合說明

### Token 類型

| 類型 | 說明 | 有效期 |
|---|---|---|
| 短效 User Token | 前端 FB Login 取得 | 約 1–2 小時 |
| 長效 User Token | 以短效 Token 換取 | 約 60 天 |
| Page Access Token | 從長效 User Token 取得 | 永久（帳號未更改時） |

### 換取長效 Token

```bash
GET https://graph.facebook.com/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id={APP_ID}
  &client_secret={APP_SECRET}
  &fb_exchange_token={短效 Token}
```

### 發文至社團

```bash
POST /fb/post
Content-Type: application/json
Authorization: Bearer <jwt>

{
  "template_id": "...",   # 選用範本（自動帶入 content）
  "message": "自訂訊息"    # 或直接填文字
}
```

> 發文使用 `/{group_id}/feed` 端點，需申請 `publish_to_groups` 權限並通過 App Review。

### 所需 FB App 權限

| 權限 | 用途 |
|---|---|
| `publish_to_groups` | 社團發文 |
| `pages_manage_posts` | 粉絲專頁發文（選用） |

---

## 排程器說明

`src/scheduler.py` 使用 `threading.Timer` 定期呼叫 `Product.auto_unpublish()`，自動將超過排程時間的商品下架。

### 開發環境（run.py）

Werkzeug reloader 會 fork 出子程序。排程器只在子程序中啟動，避免父程序重複計時：

```python
# run.py
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    from src.scheduler import start as start_scheduler
    start_scheduler()
```

### 生產環境（Gunicorn）

在 `post_fork` hook 中啟動，每個 worker 各持有一個排程執行緒：

```python
# gunicorn.py
def post_fork(server, worker):
    from src.scheduler import start as start_scheduler
    start_scheduler()
```

---

## 角色說明

| 角色 | 可存取範圍 |
|---|---|
| `admin` | 完整權限（含使用者管理、刪除） |
| `operator` | 一般操作（商品、訂單、發文；不可管理使用者） |
| `viewer` | 唯讀 |

```python
@require_role('admin')              # 僅 admin
@require_role('admin', 'operator')  # admin 或 operator
```

---

## 注意事項

| 項目 | 說明 |
|---|---|
| `conf/flask.json` | 含 `SECRET_KEY`，**勿提交至版控** |
| `docker-compose.yml` | 由 `.default` 複製而來，**勿提交至版控** |
| `FB_ACCESS_TOKEN` | 長效 Token 約 60 天到期，需定期更新 |
| 庫存扣減 | 訂單建立採「先原子扣減庫存、再建單」策略，防止並發超賣 |
| debug 模式 | 預設開啟，正式部署請改用 `ProductionConfig` |
| 預設帳號 | `admin / admin`，**首次啟動後立即修改** |
| 顧客下單頁 | `/shop/` 不需登入，掃 QR Code 即可訂購 |
