# DigitalOcean Vue 生产部署

这是 `octabit.cc` 预期使用的非 Docker 生产路径。

- Caddy 从 `apps/web-vue/dist` 提供构建后的 Vue 3 前端。
- Caddy 将 `/api/*`、`/static/previews/*` 和 `/synthesise*` 反向代理到
  `127.0.0.1:8000` 上的 Flask/Gunicorn。
- Flask/Gunicorn 继续作为私有后端，负责工作区、上传、合成、下载、预览资源和旧路由兼容。
- Flask 渲染页面仍保留在仓库中；如果切换失败，可把 Caddy 切回完整反向代理模式恢复它。

`deploy/web-flask/` 中的 Docker 文件是 Flask 后端或旧前端回退的另一条路径。除非生产计划改变，不要把 Docker 引入当前 DigitalOcean 切换流程。

## 一次性服务器形态

建议使用 `/srv/octabit` 这样的仓库检出路径、仓库本地 Python 虚拟环境、用于 Gunicorn 的
`octabit-web` systemd 服务，以及作为公开服务器的 Caddy。

Gunicorn 应保持为私有监听：

```bash
/srv/octabit/.venv/bin/python3 -m gunicorn --chdir /srv/octabit/apps/web-flask --bind 127.0.0.1:8000 --workers 2 --timeout 600 app:app
```

Vue 切换前，先用服务器常规软件源安装 Node.js 和 npm。Vue 依赖安装应使用 lockfile：

```bash
cd /srv/octabit/apps/web-vue
npm ci
npm run build
```

## Caddy 路由

生产模型使用 `Caddyfile.vue-production`：

```caddyfile
octabit.cc {
	encode zstd gzip

	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle /static/previews/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle /synthesise* {
		reverse_proxy 127.0.0.1:8000
	}

	handle {
		root * /srv/octabit/apps/web-vue/dist
		try_files {path} /index.html
		file_server
	}
}
```

这会让 Vue 应用成为公开前端，同时保留 Flask API、预览音频路由和旧合成路由。`try_files`
回退用于 Vue/Vite 浏览器路由；由于 API 路由先被处理，它不会截获 API 请求。

## 部署流程

在生产 VM 上执行：

```bash
cd /srv/octabit
git fetch --prune origin
git checkout main
git pull --ff-only origin main
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
cd apps/web-vue
npm ci
npm run build
cd /srv/octabit
sudo systemctl restart octabit-web
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

如果合并前先部署当前分支，使用辅助脚本时设置 `BRANCH=feature/vue-frontend`：

```bash
BRANCH=feature/vue-frontend deploy/digitalocean/deploy-vue-production.sh
```

合并后，辅助脚本默认目标是 `main`：

```bash
deploy/digitalocean/deploy-vue-production.sh
```

## Smoke 检查

在 VM 本机运行：

```bash
curl -fsS http://127.0.0.1:8000/api/health
test -f /srv/octabit/apps/web-vue/dist/index.html
```

Caddy reload 后运行公开检查：

```bash
curl -fsS https://octabit.cc/
curl -fsS https://octabit.cc/api/health
curl -fsSI https://octabit.cc/static/previews/pulse_50.wav
```

然后在浏览器中上传一个小 MIDI 文件，确认刷新后工作区仍可恢复，运行合成并下载 WAV，切换主题/语言，并清空排队和已转换文件。

## 回滚

如果 Vue 生产静态服务失败，保持 Flask 后端运行，并将 Caddy 站点块替换为
`Caddyfile.flask-fallback`：

```caddyfile
octabit.cc {
	encode zstd gzip
	reverse_proxy 127.0.0.1:8000
}
```

验证并重载 Caddy：

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

这会恢复旧 Flask 渲染前端，同时保留同一个 Gunicorn 后端、API、工作区存储和合成路径。
