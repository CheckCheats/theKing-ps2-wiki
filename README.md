# Slayers 2 Wiki

面向玩家的 **Slayers 2 / Project Slayers 2** 中文资料维基（静态站点）。

## 本地预览

```bash
python -m http.server 8080
# 打开 http://127.0.0.1:8080/
```

## 部署

### Cloudflare Workers（静态资源）

仓库根目录已含 `wrangler.jsonc`。Workers 构建命令保持：

```bash
npx wrangler deploy
```

无需交互；`assets.directory` 指向站点根目录。`.assetsignore` 会排除 `.git` / `tools` / 源数据等。

### GitHub Pages

1. 将本目录推送到仓库 `main` 根目录。
2. Settings → Pages → Deploy from branch → `main` / `/ (root)`。
3. 已含 `.nojekyll`，无需 Jekyll。

## 目录

```
index.html
css/
js/
assets/
p/
favicon.svg
.nojekyll
```
