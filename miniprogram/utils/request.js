const request = (options) => {
  const app = getApp();
  return new Promise((resolve, reject) => {
    wx.request({
      ...options,
      url: `${app.globalData.baseUrl}${options.url}`,
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res);
        }
      },
      fail: reject
    });
  });
};

module.exports = { request };
