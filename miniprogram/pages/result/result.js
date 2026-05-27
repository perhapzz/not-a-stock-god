const { request } = require('../../utils/request');

Page({
  data: {
    gameId: '',
    totalAssets: 0,
    initialCash: 1000000,
    profit: 0,
    profitRate: 0,
    benchmarkRate: '--',
    startDate: '',
    endDate: '',
    duration: '',
    trades: [],
    loading: true,
  },

  onLoad(options) {
    this.setData({ gameId: options.game_id });
    this.fetchResult();
  },

  fetchResult() {
    this.setData({ loading: true });
    request({ url: `/game/${this.data.gameId}/status` })
      .then((d) => {
        const profit = d.total_assets - this.data.initialCash;
        const profitRate = ((profit / this.data.initialCash) * 100).toFixed(2);
        this.setData({
          totalAssets: d.total_assets.toFixed(2),
          profit: profit.toFixed(2),
          profitRate,
          startDate: d.start_date,
          endDate: d.end_date || d.current_date,
          duration: d.duration,
        });
        // Fetch benchmark
        this.fetchBenchmark(d.start_date, d.current_date);
      })
      .finally(() => this.setData({ loading: false }));

    // Fetch trade history
    request({ url: `/game/${this.data.gameId}/trades` }).then((res) => {
      this.setData({ trades: (res.trades || []).slice(0, 20) });
    });
  },

  fetchBenchmark(start, end) {
    request({ url: `/market/benchmark?start_date=${start}&end_date=${end}` }).then((res) => {
      if (res.change_pct !== undefined) {
        this.setData({ benchmarkRate: res.change_pct });
      }
    });
  },

  goHome() {
    wx.reLaunch({ url: '/pages/index/index' });
  },

  goRank() {
    wx.navigateTo({ url: '/pages/rank/rank' });
  },

  onShareAppMessage() {
    return {
      title: `我在"我不是股神"赚了${this.data.profitRate}%！`,
      path: '/pages/index/index',
    };
  },
});
