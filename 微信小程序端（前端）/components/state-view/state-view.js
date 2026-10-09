Component({
  properties: {
    loading: { type: Boolean, value: false },
    loadingText: { type: String, value: '加载中...' },
    empty: { type: Boolean, value: false },
    emptyText: { type: String, value: '暂无数据' },
    error: { type: Boolean, value: false },
    errorText: { type: String, value: '加载失败，请稍后重试' },
    showRetry: { type: Boolean, value: true }
  },
  methods: {
    onRetryTap() {
      this.triggerEvent('retry')
    }
  }
})

