const util = require('../../utils/util')

const audioManager = wx.getBackgroundAudioManager()

Page({
  data: {
    mediaUrl: '',
    mediaType: 'video',
    mediaTypeLabel: '视频',
    pageTitle: '媒体播放',
    mediaHint: '请确保当前设备网络正常',
    audioPlaying: false,
    posterUrl: '/static/default-dish.png'
  },

  onLoad(options) {
    const rawUrl = options.url ? decodeURIComponent(options.url) : ''
    const mediaUrl = util.formatImageUrl(rawUrl)
    const mediaType = options.type === 'audio' ? 'audio' : 'video'

    audioManager.onPlay(() => {
      this.setData({ audioPlaying: true })
    })
    audioManager.onPause(() => {
      this.setData({ audioPlaying: false })
    })
    audioManager.onStop(() => {
      this.setData({ audioPlaying: false })
    })
    audioManager.onEnded(() => {
      this.setData({ audioPlaying: false })
    })
    audioManager.onError((err) => {
      console.error('音频播放失败', err)
      wx.showToast({ title: '音频播放失败，请检查地址', icon: 'none' })
      this.setData({ audioPlaying: false })
    })

    this.setData({
      mediaUrl,
      mediaType,
      mediaTypeLabel: mediaType === 'audio' ? '音频' : '视频',
      pageTitle: mediaType === 'audio' ? '音频介绍' : '视频介绍',
      mediaHint: mediaType === 'audio' ? '点击下方按钮开始或暂停播放' : '支持全屏播放，视频内音频将同步播放',
      posterUrl: util.formatImageUrl('/static/default-dish.png')
    })

    if (!mediaUrl) {
      wx.showToast({ title: '媒体地址为空', icon: 'none' })
      return
    }

    if (mediaType === 'audio') {
      this.startAudio()
    }
  },

  onUnload() {
    if (this.data.mediaType === 'audio') {
      audioManager.stop()
      this.setData({ audioPlaying: false })
    }
  },

  startAudio() {
    if (!this.data.mediaUrl) return
    audioManager.title = this.data.pageTitle
    audioManager.epname = this.data.pageTitle
    audioManager.singer = '校园食堂点餐'
    audioManager.coverImgUrl = util.formatImageUrl('/static/default-dish.png')
    audioManager.src = this.data.mediaUrl
    this.setData({ audioPlaying: true })
  },

  onToggleAudio() {
    if (!this.data.mediaUrl) return
    if (this.data.audioPlaying) {
      audioManager.pause()
      this.setData({ audioPlaying: false })
      return
    }
    if (audioManager.src !== this.data.mediaUrl) {
      this.startAudio()
      return
    }
    audioManager.play()
    this.setData({ audioPlaying: true })
  },

  onVideoLoaded(e) {
    console.log('视频元数据加载完成', this.data.mediaUrl, e)
  },

  onVideoPlay() {
    console.log('开始播放视频', this.data.mediaUrl)
  },

  onVideoPause() {
    console.log('暂停播放视频', this.data.mediaUrl)
  },

  onFullscreenChange(e) {
    console.log('全屏状态变化', e)
  },

  onVideoError(e) {
    console.error('视频播放失败', this.data.mediaUrl, e)
    const errCode = e && e.detail ? e.detail.errMsg || e.detail.errCode || '' : ''
    wx.showModal({
      title: '视频播放失败',
      content: `当前地址：${this.data.mediaUrl}\n错误信息：${errCode || '未知错误'}\n\n若浏览器能播但小程序不能播，通常是视频编码不兼容。请将视频转为 H.264 视频编码 + AAC 音频编码的 MP4。`,
      showCancel: false
    })
  }
})

