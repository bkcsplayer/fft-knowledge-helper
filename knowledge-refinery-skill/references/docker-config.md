# Docker Configuration — Knowledge Refinery

## 开发环境

### docker-compose.yml

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app
      - ./knowledge-vault:/app/knowledge-vault
      - ./attachments:/app/attachments
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - refinery-net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host 0.0.0.0
    networks:
      - refinery-net

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DB_NAME:-knowledge_refinery}
      POSTGRES_USER: ${DB_USER:-refinery}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-refinery_dev_2026}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-refinery}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - refinery-net

volumes:
  pgdata:

networks:
  refinery-net:
    driver: bridge
```

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 创建存储目录
RUN mkdir -p /app/knowledge-vault /app/attachments

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### backend/requirements.txt

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
sqlalchemy[asyncio]==2.0.*
asyncpg==0.30.*
alembic==1.14.*
pydantic==2.10.*
pydantic-settings==2.7.*
httpx==0.28.*
python-multipart==0.0.18
python-slugify==8.0.*
pyyaml==6.0.*
beautifulsoup4==4.12.*
Pillow==11.*
```

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### frontend/package.json (核心依赖)

```json
{
  "name": "knowledge-refinery-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "axios": "^1.7.9",
    "lucide-react": "^0.460.0",
    "react-dropzone": "^14.3.5",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "vite": "^6.0.3"
  }
}
```

---

## 生产环境

### docker-compose.prod.yml

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    volumes:
      - ./knowledge-vault:/app/knowledge-vault
      - ./attachments:/app/attachments
    env_file: .env.prod
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    networks:
      - refinery-net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: always
    networks:
      - refinery-net

  db:
    image: postgres:16-alpine
    restart: always
    volumes:
      - pgdata_prod:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - refinery-net

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/conf.d/default.conf
      - /www/server/panel/vhost/cert:/etc/nginx/ssl  # 宝塔 SSL 证书路径
    depends_on:
      - backend
      - frontend
    networks:
      - refinery-net

volumes:
  pgdata_prod:

networks:
  refinery-net:
    driver: bridge
```

### frontend/Dockerfile.prod

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### nginx/nginx.prod.conf (宝塔部署)

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name your-domain.com;

    # 强制 HTTPS (宝塔自动管理 SSL)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书 (宝塔管理)
    ssl_certificate     /etc/nginx/ssl/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/your-domain.com/privkey.pem;

    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 上传文件大小限制
        client_max_body_size 20M;

        # 长连接 (管线执行可能较久)
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # 静态文件 (附件访问)
    location /attachments/ {
        alias /app/attachments/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 环境变量

### .env.example (开发)

```bash
# Database
DB_NAME=knowledge_refinery
DB_USER=refinery
DB_PASSWORD=refinery_dev_2026
DB_HOST=db
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Models
MODEL_EXTRACT=anthropic/claude-3.5-sonnet
MODEL_VERIFY_GROK=x-ai/grok-3
MODEL_VERIFY_GEMINI=google/gemini-2.5-pro
MODEL_ANALYZE=anthropic/claude-opus-4-6

# Storage
KNOWLEDGE_VAULT_PATH=/app/knowledge-vault
ATTACHMENTS_PATH=/app/attachments

# App
APP_ENV=development
APP_SECRET_KEY=dev-secret-change-me
CORS_ORIGINS=http://localhost:3000
```

### .env.prod (生产) — 不要提交到 Git

```bash
DB_NAME=knowledge_refinery
DB_USER=refinery
DB_PASSWORD=<strong-random-password>
DB_HOST=db
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://refinery:<password>@db:5432/knowledge_refinery

OPENROUTER_API_KEY=sk-or-v1-<your-key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

MODEL_EXTRACT=anthropic/claude-3.5-sonnet
MODEL_VERIFY_GROK=x-ai/grok-3
MODEL_VERIFY_GEMINI=google/gemini-2.5-pro
MODEL_ANALYZE=anthropic/claude-opus-4-6

KNOWLEDGE_VAULT_PATH=/app/knowledge-vault
ATTACHMENTS_PATH=/app/attachments

APP_ENV=production
APP_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://your-domain.com
```

---

## 宝塔部署步骤

```
1. SSH 到 VPS
2. 安装 Docker + Docker Compose (宝塔 Docker Manager 插件)
3. git clone 项目到 /www/wwwroot/knowledge-refinery/
4. cp .env.example .env.prod (修改密码和 API Key)
5. docker compose -f docker-compose.prod.yml up -d --build
6. 宝塔面板 → 网站 → 添加反向代理 (或直接用 compose 里的 nginx)
7. 宝塔面板 → SSL → 申请 Let's Encrypt 证书
8. 访问 https://your-domain.com 测试
```

## .gitignore

```
.env
.env.prod
__pycache__/
*.pyc
node_modules/
dist/
knowledge-vault/*.md
attachments/*
!knowledge-vault/.gitkeep
!attachments/.gitkeep
pgdata/
```
