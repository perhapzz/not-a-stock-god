const { request } = require('../../utils/request');

Page({
  data: {
    gameId: '',
    currentDate: '',
    startDate: '',
    endDate: '',
    cash: 1000000,
    positions: [],
    todayKline: null,
    stocks: [],
    filteredStocks: [],
    selectedStock: '',
    searchKeyword: '',
    tradeAmount: '',
    totalAssets: 1000000,
    profitRate: 0,
    gameOver: false,
    loading: false,
    tradingLoading: false,
    showStockList: false,
    showTradeHistory: false,
    trades: [],
  },

  onLoad(options) {
    this.setData({ gameId: options.game_id });
    this.fetchStocks();
    this.fetchStatus();
  },

  fetchStocks() {
    request({ url: '/market/stocks' }).then((res) => {
      this.setData({ stocks: res.stocks || [], filteredStocks: (res.stocks || []).slice(0, 20) });
    });
  },

  fetchStatus() {
    this.setData({ loading: true });
    request({ url: `/game/${this.data.gameId}/status` })
      .then((d) => {
        if (d.error) {
          wx.showToast({ title: d.error, icon: 'none' });
          return;
        }
        this.setData({
          currentDate: d.current_date,
          startDate: d.start_date,
          endDate: d.end_date,
          cash: d.cash,
          positions: d.positions || [],
          totalAssets: d.total_assets,
          profitRate: d.profit_rate,
          gameOver: d.game_over || false,
        });
        if (d.game_over) {
          wx.redirectTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
        }
        // Refresh kline if stock selected
        if (this.data.selectedStock) {
          this.fetchKline(this.data.selectedStock);
        }
      })
      .finally(() => this.setData({ loading: false }));
  },

  fetchKline(symbol) {
    request({ url: `/market/kline/${symbol}?date=${this.data.currentDate}` }).then((res) => {
      if (!res.error) {
        this.setData({ todayKline: res });
      } else {
        this.setData({ todayKline: null });
        wx.showToast({ title: '该股票当日无数据', icon: 'none' });
      }
    });
  },

  onSearchInput(e) {
    const keyword = e.detail.value;
    this.setData({ searchKeyword: keyword, showStockList: true });
    if (keyword) {
      const filtered = this.data.stocks.filter(
        (s) => s.symbol.includes(keyword) || s.name.includes(keyword)
      ).slice(0, 20);
      this.setData({ filteredStocks: filtered });
    } else {
      this.setData({ filteredStocks: this.data.stocks.slice(0, 20) });
    }
  },

  toggleStockList() {
    this.setData({ showStockList: !this.data.showStockList });
  },

  onStockSelect(e) {
    const symbol = e.currentTarget.dataset.symbol;
    const name = e.currentTarget.dataset.name;
    this.setData({ selectedStock: symbol, searchKeyword: `${name}(${symbol})`, showStockList: false });
    this.fetchKline(symbol);
  },

  onAmountInput(e) {
    this.setData({ tradeAmount: e.detail.value });
  },

  buy() {
    this.doTrade('buy');
  },

  sell() {
    this.doTrade('sell');
  },

  doTrade(action) {
    if (!this.data.selectedStock) {
      wx.showToast({ title: '请先选择股票', icon: 'none' });
      return;
    }
    const amount = parseInt(this.data.tradeAmount);
    if (!amount || amount % 100 !== 0) {
      wx.showToast({ title: '请输入100的整数倍', icon: 'none' });
      return;
    }
    this.setData({ tradingLoading: true });
    request({
      url: `/game/${this.data.gameId}/trade`,
      method: 'POST',
      data: { symbol: this.data.selectedStock, action, amount },
    })
      .then((res) => {
        if (res.success) {
          wx.showToast({ title: res.message, icon: 'success' });
          this.setData({ tradeAmount: '' });
          this.fetchStatus();
        } else {
          wx.showToast({ title: res.message || '交易失败', icon: 'none' });
        }
      })
      .finally(() => this.setData({ tradingLoading: false }));
  },

  nextDay() {
    this.setData({ loading: true });
    request({ url: `/game/${this.data.gameId}/next-day`, method: 'POST' })
      .then((res) => {
        if (res.game_over) {
          wx.redirectTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
        } else {
          this.fetchStatus();
        }
      })
      .finally(() => this.setData({ loading: false }));
  },

  fastForward() {
    wx.showModal({
      title: '快进确认',
      content: '确定要快进到游戏结束吗？快进期间不能交易。',
      success: (res) => {
        if (res.confirm) {
          this.setData({ loading: true });
          request({ url: `/game/${this.data.gameId}/fast-forward`, method: 'POST' })
            .then((res) => {
              wx.redirectTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
            })
            .finally(() => this.setData({ loading: false }));
        }
      },
    });
  },

  settle() {
    wx.showModal({
      title: '提前结算',
      content: '确定要提前结算吗？',
      success: (res) => {
        if (res.confirm) {
          request({ url: `/game/${this.data.gameId}/settle`, method: 'POST' }).then(() => {
            wx.redirectTo({ url: `/pages/result/result?game_id=${this.data.gameId}` });
          });
        }
      },
    });
  },

  showTrades() {
    request({ url: `/game/${this.data.gameId}/trades` }).then((res) => {
      this.setData({ trades: res.trades || [], showTradeHistory: true });
    });
  },

  hideTradeHistory() {
    this.setData({ showTradeHistory: false });
  },

  quickAmount(e) {
    const pct = e.currentTarget.dataset.pct;
    if (!this.data.todayKline || !this.data.todayKline.close) return;
    const price = this.data.todayKline.close;
    const maxShares = Math.floor((this.data.cash * pct) / price / 100) * 100;
    this.setData({ tradeAmount: String(maxShares > 0 ? maxShares : 100) });
  },
});
