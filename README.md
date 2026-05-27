# 我不是股神 🕐

穿越时空的A股模拟交易小程序。选择一个历史日期，用100万虚拟资金在真实历史数据上进行股票交易，看看你能跑赢大盘吗？

## 功能特性

- 🎮 **时间穿越**：选择2010-2024年任意日期开始游戏
- 📊 **真实数据**：基于AKShare获取A股日K线历史数据
- 💰 **模拟交易**：买入/卖出操作，支持T+1规则，100股整数倍
- 📈 **大盘对比**：结算时自动对比上证指数收益率
- ⏩ **快进功能**：可快进到游戏结束
- 🏆 **排行榜**：按收益率全球排名
- ⏱️ **多时长**：支持1个月/3个月/1年游戏周期

## 技术栈

- **后端**: FastAPI + SQLite + AKShare
- **前端**: 微信小程序 + TDesign组件库
- **部署**: Docker + docker-compose

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
docker-compose up -d --build
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | SQLite数据库路径 | `data/game.db` |

### 前端配置

修改 `miniprogram/utils/config.js` 中的 `baseUrl` 为你的后端地址：

```javascript
const config = {
  development: { baseUrl: 'http://localhost:8000' },
  production: { baseUrl: 'https://your-domain.com' },
};
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/game/start` | 开始新游戏 |
| GET | `/game/{id}/status` | 获取游戏状态 |
| POST | `/game/{id}/trade` | 交易（买入/卖出） |
| POST | `/game/{id}/next-day` | 推进到下一交易日 |
| POST | `/game/{id}/fast-forward` | 快进到游戏结束 |
| POST | `/game/{id}/settle` | 提前结算 |
| GET | `/game/{id}/trades` | 获取交易记录 |
| GET | `/market/stocks` | 获取股票列表 |
| GET | `/market/kline/{symbol}?date=` | 获取K线数据 |
| GET | `/market/benchmark?start_date=&end_date=` | 获取大盘指数 |
| GET | `/rank` | 获取排行榜 |
| GET | `/health` | 健康检查 |

## 上线前需要做的

1. 在[微信公众平台](https://mp.weixin.qq.com/)注册小程序账号
2. 获取 AppID，替换 `project.config.json` 中的 `appid`
3. 在小程序后台配置合法域名（你的后端域名）
4. 部署后端到服务器，配置 HTTPS
5. 修改 `miniprogram/utils/config.js` 中 production 的 `baseUrl`
6. 使用微信开发者工具上传代码并提审

## 免责声明

⚠️ 本小程序仅为历史数据模拟游戏，所有交易均为虚拟操作，不构成任何投资建议。股市有风险，入市需谨慎。
