// API 配置文件
const ENV = 'development'; // 'development' | 'production'

const config = {
  development: {
    baseUrl: 'http://localhost:8000',
  },
  production: {
    baseUrl: 'https://your-backend-domain.com',
  },
};

module.exports = config[ENV];
