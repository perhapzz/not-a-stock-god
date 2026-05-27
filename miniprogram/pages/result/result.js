const app = getApp();

Page({
  data: {
    gameId: '',
    totalAssets: 0,
    initialCash: 1000000,
    profit: 0,
    profitRate: 0,
    rank: 0,
    trades: []
  },

  onLoad(options) {
    this.setData({ gameId: options.game_id });
    this.fetchResult();
  },

  fetchResult() {
    wx.request({
      url: `${app.globalData.baseUrl}/game/${this.data.gameId}/status`,
      success: (res) => {
        const d = res.data;
        const profit = d.total_assets - this.data.initialCash;
        const profitRate = (profit / this.data.initialCash * 100).toFixed(2);
        this.setData({
          totalAssets: d.total_assets,
          profit: profit,
          profitRate: profitRate,
          rank: d.rank || '-'
        });
      }
    });
  },

  goHome() {
    wx.navigateTo({ url: '/pages/index/index' });
  },

  goRank() {
    wx.navigateTo({ url: '/pages/rank/rank' });
  },

  shareResult() {
    // 分享功能
  }
});
