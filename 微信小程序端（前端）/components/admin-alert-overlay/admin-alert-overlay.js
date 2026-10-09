Component({
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    alert: {
      type: Object,
      value: null
    },
    queueLength: {
      type: Number,
      value: 0
    }
  },

  data: {
    closing: false
  },

  methods: {
    onMaskTap() {},

    onLater() {
      this.triggerEvent('later')
    },

    onView() {
      this.triggerEvent('view', this.properties.alert || {})
    }
  }
})

