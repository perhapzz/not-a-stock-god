const { request } = require('../../utils/request');

Page({
  data: {
    rankList: [],
    loading: false,
  },

  onLoad() {
    this.fetchRank();
  },

  onPullDownRefresh() {
    this.fetchRank();
  },

  fetchRank() {
    this.setData({ loading: true });
    request({ url: '/rank' })
      .then((res) => {
        this.setData({ rankList: res.ranks || [] });
      })
      .finally(() => {
        this.setData({ loading: false });
        wx.stopPullDownRefresh();
      });
  },

  goHome() {
    wx.reLaunch({ url: '/pages/index/index' });
  },
});
