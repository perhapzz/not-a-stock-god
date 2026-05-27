const app = getApp();

Page({
  data: {
    gameId: '',
    currentDate: '',
    cash: 1000000,
    positions: [],
    todayKline: {},
    stocks: [],
    selectedStock: '',
    tradeAmount: '',
    totalAssets: 1000000,
    gameOver: false
  },

  onLoad(options) {
    this.setData({ gameId: options.game_id });
    this.fetchStatus();
  },

  fetchStatus() {
    wx.request({
      url: `${app.globalData.baseUrl}/game/${this.data.gameId}/status`,
      success: (res) => {
        const d = res.data;
        this.setData({
          currentDate: d.current_date,
          cash: d.cash,
          positions: d.positions || [],
          totalAssets: d.total_assets,
          gameOver: d.game_over || false
        });
        if (d.game_over) {
          wx.navigateTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
        }
      }
    });
  },

  fetchKline(symbol) {
    wx.request({
      url: `${app.globalData.baseUrl}/market/kline/${symbol}?date=${this.data.currentDate}`,
      success: (res) => {
        this.setData({ todayKline: res.data });
      }
    });
  },

  onStockSelect(e) {
    const symbol = e.currentTarget.dataset.symbol;
    this.setData({ selectedStock: symbol });
    this.fetchKline(symbol);
  },

  onAmountInput(e) {
    this.setData({ tradeAmount: e.detail.value });
  },

  buy() {
    this.trade('buy');
  },

  sell() {
    this.trade('sell');
  },

  trade(action) {
    const amount = parseInt(this.data.tradeAmount);
    if (!amount || amount % 100 !== 0) {
      wx.showToast({ title: '请输入100的整数倍', icon: 'none' });
      return;
    }
    wx.request({
      url: `${app.globalData.baseUrl}/game/${this.data.gameId}/trade`,
      method: 'POST',
      data: {
        symbol: this.data.selectedStock,
        action: action,
        amount: amount
      },
      success: (res) => {
        if (res.data.success) {
          wx.showToast({ title: `${action === 'buy' ? '买入' : '卖出'}成功` });
          this.fetchStatus();
        } else {
          wx.showToast({ title: res.data.message || '交易失败', icon: 'none' });
        }
      }
    });
  },

  nextDay() {
    wx.request({
      url: `${app.globalData.baseUrl}/game/${this.data.gameId}/next-day`,
      method: 'POST',
      success: (res) => {
        if (res.data.game_over) {
          wx.navigateTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
        } else {
          this.fetchStatus();
          if (this.data.selectedStock) {
            this.fetchKline(this.data.selectedStock);
          }
        }
      }
    });
  },

  settle() {
    wx.request({
      url: `${app.globalData.baseUrl}/game/${this.data.gameId}/settle`,
      method: 'POST',
      success: () => {
        wx.navigateTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
      }
    });
  }
});
