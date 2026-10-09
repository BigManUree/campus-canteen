# 校园食堂管理后台重构说明

本项目已重构为基于 `Vue 3 + Vite + Element Plus + Pinia + Vue Router` 的 Web 管理后台。

## 启动方式

```bash
npm install
npm run dev
```

## 当前已完成

- 新建 Vue 3 + Vite 工程入口
- 接入 Element Plus、Pinia、Vue Router
- 重建请求层、鉴权、后台布局
- 完成登录页
- 完成数据看板、订单管理、退款管理首批页面
- 其余模块已完成骨架页面与菜单路由占位

## 接口基准

接口对接以 `campus_canteen_apifox.json` 为准，默认后端地址：`http://localhost:8000`

## 后续模块

后续可继续在现有骨架上完善：

- 用户管理
- 菜品管理
- 档口管理
- 分类管理
- 优惠券管理
- 活动管理
- 评价管理
- 通知管理
- FAQ 管理
- 统计分析
- 报表导出
- 商家账号
- 排队管理

