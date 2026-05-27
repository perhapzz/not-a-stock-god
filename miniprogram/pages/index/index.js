const app = getApp();

Page({
  data: {
    selectedDate: '',
    datePickerVisible: false,
    duration: '1month',
    stocks: [],
    loading: false
  },

  onLoad() {
    this.fetchStocks();
  },

  fetchStocks() {
    this.setData({ loading: true });
    wx.request({
      url: `${app.globalData.baseUrl}/market/stocks`,
      success: (res) => {
        this.setData({ stocks: res.data.stocks || [] });
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  },

  onDatePickerShow() {
    this.setData({ datePickerVisible: true });
  },

  onDateConfirm(e) {
    this.setData({
      selectedDate: e.detail.value,
      datePickerVisible: false
    });
  },

  onDateCancel() {
    this.setData({ datePickerVisible: false });
  },

  onDurationChange(e) {
    this.setData({ duration: e.currentTarget.dataset.duration });
  },

  startGame() {
    if (!this.data.selectedDate) {
      wx.showToast({ title: '请选择穿越日期', icon: 'none' });
      return;
    }

    wx.request({
      url: `${app.globalData.baseUrl}/game/start`,
      method: 'POST',
      data: {
        start_date: this.data.selectedDate,
        duration: this.data.duration
      },
      success: (res) => {
        if (res.data.game_id) {
          wx.navigateTo({
            url: `/pages/trading/trading?game_id=${res.data.game_id}`
          });
        }
      },
      fail: () => {
        wx.showToast({ title: '开始游戏失败', icon: 'none' });
      }
    });
  }
});
