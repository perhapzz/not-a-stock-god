const config = require('./config');

const request = (options) => {
  return new Promise((resolve, reject) => {
    wx.showNavigationBarLoading();
    wx.request({
      ...options,
      url: `${config.baseUrl}${options.url}`,
      header: {
        'Content-Type': 'application/json',
        ...options.header,
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 429) {
          wx.showToast({ title: '请求太频繁，请稍后再试', icon: 'none' });
          reject(res);
        } else {
          wx.showToast({ title: res.data?.error || '请求失败', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      },
      complete: () => {
        wx.hideNavigationBarLoading();
      },
    });
  });
};

module.exports = { request };
