const app = getApp();

Page({
  data: {
    rankList: [],
    loading: false
  },

  onLoad() {
    this.fetchRank();
  },

  fetchRank() {
    this.setData({ loading: true });
    wx.request({
      url: `${app.globalData.baseUrl}/rank`,
      success: (res) => {
        this.setData({ rankList: res.data.ranks || [] });
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  }
});
