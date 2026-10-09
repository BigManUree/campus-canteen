"""
订单相关配置
可配置化的超时时间设置
"""

class OrderConfig:
    """订单配置"""
    
    # 未支付订单自动取消时间（分钟）
    UNPAID_ORDER_TIMEOUT_MINUTES = 30
    
    # 待取餐订单超时提醒时间（小时）
    PICKUP_TIMEOUT_HOURS = 2
    
    # 定时任务执行间隔
    AUTO_CANCEL_CHECK_INTERVAL_MINUTES = 5  # 每5分钟检查一次未支付订单
    PICKUP_REMIND_CHECK_INTERVAL_MINUTES = 10  # 每10分钟检查一次待取餐超时
    
    # 库存锁定相关
    INVENTORY_LOCK_ENABLED = True  # 是否启用库存预扣机制
    
    @classmethod
    def get_unpaid_timeout_minutes(cls) -> int:
        """获取未支付订单超时时间（分钟）"""
        return cls.UNPAID_ORDER_TIMEOUT_MINUTES
    
    @classmethod
    def get_pickup_timeout_hours(cls) -> int:
        """获取待取餐超时提醒时间（小时）"""
        return cls.PICKUP_TIMEOUT_HOURS
    
    @classmethod
    def set_unpaid_timeout_minutes(cls, minutes: int):
        """设置未支付订单超时时间"""
        if minutes < 5:
            raise ValueError("超时时间不能少于5分钟")
        cls.UNPAID_ORDER_TIMEOUT_MINUTES = minutes
    
    @classmethod
    def set_pickup_timeout_hours(cls, hours: int):
        """设置待取餐超时提醒时间"""
        if hours < 1:
            raise ValueError("超时时间不能少于1小时")
        cls.PICKUP_TIMEOUT_HOURS = hours


# 全局配置实例
order_config = OrderConfig()

