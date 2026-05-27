const { request } = require('../../utils/request');

Page({
  data: {
    selectedDate: '',
    datePickerVisible: false,
    duration: '1month',
    loading: false,
  },

  onLoad() {},

  onDatePickerShow() {
    this.setData({ datePickerVisible: true });
  },

  onDateConfirm(e) {
    this.setData({
      selectedDate: e.detail.value,
      datePickerVisible: false,
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

    this.setData({ loading: true });
    request({
      url: '/game/start',
      method: 'POST',
      data: {
        start_date: this.data.selectedDate,
        duration: this.data.duration,
      },
    })
      .then((res) => {
        if (res.game_id) {
          wx.navigateTo({
            url: `/pages/trading/trading?game_id=${res.game_id}`,
          });
        }
      })
      .catch(() => {
        wx.showToast({ title: '开始游戏失败', icon: 'none' });
      })
      .finally(() => {
        this.setData({ loading: false });
      });
  },

  goRank() {
    wx.navigateTo({ url: '/pages/rank/rank' });
  },
});
