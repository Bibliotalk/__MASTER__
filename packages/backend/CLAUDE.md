# SecondMe 集成项目

## 应用信息

- **App Name**: 諸子云 Bibliotalk
- **Client ID**: 78699a15-****-****-****-********3438

## API 文档

开发时请参考官方文档：

| 文档        | 链接                                                          |
| ----------- | ------------------------------------------------------------- |
| 快速入门    | https://develop-docs.second.me/zh/docs                        |
| OAuth2 认证 | https://develop-docs.second.me/zh/docs/authentication/oauth2  |
| API 参考    | https://develop-docs.second.me/zh/docs/api-reference/secondme |
| 错误码      | https://develop-docs.second.me/zh/docs/errors                 |

## 关键信息

- **API 基础 URL**: https://app.mindos.com/gate/lab
- **OAuth 授权 URL**: https://go.second.me/oauth/
- **Access Token 有效期**: 2 小时
- **Refresh Token 有效期**: 30 天

> 所有 API 端点配置请参考 `.secondme/state.json` 中的 `api` 和 `docs` 字段

## 已选模块

本项目已集成以下 SecondMe 功能模块：

| 模块      | 说明                        | 状态             |
| --------- | --------------------------- | ---------------- |
| `auth`    | OAuth 认证                  | ✅ 已启用（必选） |
| `profile` | 用户信息展示                | ✅ 已启用         |
| `chat`    | 对话功能                    | ✅ 已启用         |
| `act`     | 结构化动作判断（返回 JSON） | ✅ 已启用         |
| `note`    | 笔记功能                    | ✅ 已启用         |

## 权限列表 (Scopes)

本应用拥有以下权限：

| 权限  | 说明     | 状态     |
| ----- | -------- | -------- |
| `all` | 全部权限 | ✅ 已授权 |

包含以下具体权限：
- `user.info` - 用户基础信息
- `user.info.shades` - 用户兴趣标签
- `user.info.softmemory` - 用户软记忆
- `chat` - 聊天功能
- `note.add` - 添加笔记

## 环境变量

在开发时，请确保以下环境变量已设置（从 `.secondme/state.json` 读取）：

```env
SECONDME_CLIENT_ID=78699a15-1122-4a26-89ee-970440953438
SECONDME_CLIENT_SECRET=edc4f7e392aee3a41621197063e12ea75f9e110d0094c465a3cd2310706272c6
SECONDME_REDIRECT_URI=http://localhost:3000/api/auth/callback
DATABASE_URL=file:./dev.db
```

## 开发注意事项

1. **敏感信息保护**: 请确保 `.secondme/` 目录已添加到 `.gitignore`
2. **数据库**: 当前使用 SQLite (`file:./dev.db`)，生产环境建议使用 PostgreSQL 或 MySQL
3. **回调地址**: 开发环境使用 `http://localhost:3000/api/auth/callback`，生产环境使用 `https://bibliotalk.vercel.app/api/auth/callback`
