# 静态文件目录说明

此目录用于存放前端需要的静态资源文件。

## 当前缺失的文件

前端小程序需要以下 banner 图片，但目前不存在：

- `banner1.jpg` - 首页轮播图1
- `banner2.jpg` - 首页轮播图2  
- `banner3.jpg` - 首页轮播图3

## 解决方案

### 方案1：创建占位图片（临时）

```bash
# 在 static 目录下创建空白图片文件
echo. > banner1.jpg
echo. > banner2.jpg
echo. > banner3.jpg
```

### 方案2：使用真实图片（推荐）

1. 准备 3 张轮播图（建议尺寸：750x400 像素）
2. 重命名为 `banner1.jpg`、`banner2.jpg`、`banner3.jpg`
3. 复制到此目录

### 方案3：修改前端代码

如果不需要轮播图，可以在前端代码中移除或注释掉相关代码。

## 访问路径

- 本地：`http://localhost:8000/static/banner1.jpg`
- 生产：`https://your-domain.com/static/banner1.jpg`

## 注意事项

⚠️ **微信小程序要求使用 HTTPS**

开发环境可以在小程序开发工具中关闭"不校验合法域名"选项。
生产环境必须配置 HTTPS 证书。

