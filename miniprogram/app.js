const config = require('./utils/config');

App({
  globalData: {
    baseUrl: config.baseUrl,
    initialCash: 1000000,
  },
  onLaunch() {
    console.log('我不是股神 - 启动');
  },
});
