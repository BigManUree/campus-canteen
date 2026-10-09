export const menuGroups = [
  {
    title: '总览看板',
    items: [
  { path: '/dashboard', name: 'dashboard', title: '数据看板', icon: 'DataAnalysis' },
      { path: '/statistics', name: 'statistics', title: '统计分析', icon: 'TrendCharts' },
      { path: '/export', name: 'export', title: '报表导出', icon: 'Download' }
    ]
  },
  {
    title: '交易运营',
    items: [
  { path: '/orders', name: 'orders', title: '订单管理', icon: 'Tickets' },
  { path: '/refunds', name: 'refunds', title: '退款管理', icon: 'WalletFilled' },
      { path: '/notifications', name: 'notifications', title: '通知中心', icon: 'Bell' },
      { path: '/queues', name: 'queues', title: '排队看板', icon: 'Histogram' }
    ]
  },
  {
    title: '内容与商品',
    items: [
  { path: '/dishes', name: 'dishes', title: '菜品管理', icon: 'Food' },
  { path: '/activities', name: 'activities', title: '活动管理', icon: 'Present' },
  { path: '/categories', name: 'categories', title: '分类管理', icon: 'CollectionTag' },
  { path: '/coupons', name: 'coupons', title: '优惠券管理', icon: 'Discount' },
      { path: '/faqs', name: 'faqs', title: '常见问题', icon: 'QuestionFilled' }
    ]
  },
  {
    title: '组织配置',
    items: [
      { path: '/users', name: 'users', title: '用户管理', icon: 'User' },
      { path: '/canteens', name: 'canteens', title: '档口管理', icon: 'OfficeBuilding' },
      { path: '/messages', name: 'messages', title: '消息中心', icon: 'ChatDotRound' }
    ]
  }
]

export const menuItems = menuGroups.flatMap((group) => group.items)
