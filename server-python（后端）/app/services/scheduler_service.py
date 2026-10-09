"""
定时任务调度服务
处理订单自动取消、库存释放、超时提醒等定时任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.logging import logger
from app.core.order_config import order_config
from app.db.session import SessionLocal
from app.models.order import Order
from app.services import inventory_service


# 全局调度器实例
scheduler = BackgroundScheduler()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # 不在这里关闭，由任务函数关闭


def auto_cancel_unpaid_orders():
    """自动取消未支付订单（可配置超时时间）"""
    db = get_db()
    try:
        timeout_minutes = order_config.get_unpaid_timeout_minutes()
        logger.info(f"🔄 开始执行：自动取消未支付订单任务（超时时间：{timeout_minutes}分钟）")
        
        # 释放超时订单的库存（同时会取消订单）
        released_count = inventory_service.check_and_release_expired_locks(db, timeout_minutes=timeout_minutes)
        
        if released_count > 0:
            logger.info(f"✅ 自动取消了 {released_count} 个未支付订单")
        else:
            logger.debug("✅ 没有需要取消的未支付订单")
            
    except Exception as e:
        logger.error(f"❌ 自动取消未支付订单任务失败: {e}", exc_info=True)
    finally:
        db.close()


def remind_pickup_timeout():
    """提醒待取餐超时订单（可配置超时时间）"""
    db = get_db()
    try:
        timeout_hours = order_config.get_pickup_timeout_hours()
        logger.info(f"🔄 开始执行：待取餐超时提醒任务（超时时间：{timeout_hours}小时）")
        
        # 查找待取餐超过指定时间的订单
        timeout_time = datetime.now() - timedelta(hours=timeout_hours)
        
        timeout_orders = db.query(Order).filter(
            and_(
                Order.order_status == 2,  # 待取餐
                Order.ready_time < timeout_time  # 制作完成超过指定时间
            )
        ).all()
        
        if not timeout_orders:
            logger.debug("✅ 没有待取餐超时的订单")
            return
        
        # 发送提醒通知
        from app.api.v1.websocket import notify_pickup_timeout
        
        for order in timeout_orders:
            try:
                # WebSocket 推送提醒
                import asyncio
                asyncio.run(notify_pickup_timeout(
                    order_id=order.order_id,
                    order_no=order.order_no,
                    user_id=order.user_id,
                    timeout_hours=timeout_hours
                ))
                
                logger.info(f"✅ 已发送取餐超时提醒: order_id={order.order_id}, order_no={order.order_no}")
                
            except Exception as e:
                logger.warning(f"⚠️ 发送取餐超时提醒失败 order_id={order.order_id}: {e}")
        
        logger.info(f"✅ 共发送 {len(timeout_orders)} 个取餐超时提醒")
        
    except Exception as e:
        logger.error(f"❌ 待取餐超时提醒任务失败: {e}", exc_info=True)
    finally:
        db.close()


def check_refund_approvals():
    """检查退款审批时效"""
    db = get_db()
    try:
        logger.info("🔄 开始执行：检查退款审批时效任务")
        
        from app.services.refund_service import RefundService
        import asyncio
        
        # 检查待处理的退款申请
        asyncio.run(RefundService.check_pending_refunds(db))
        
        logger.debug("✅ 检查退款审批时效任务完成")
        
    except Exception as e:
        logger.error(f"❌ 检查退款审批时效任务失败: {e}", exc_info=True)
    finally:
        db.close()


def cleanup_old_notifications():
    """清理旧通知（已读且超过30天）"""
    db = get_db()
    try:
        logger.info("🔄 开始执行：清理旧通知任务")
        
        from app.services.notification_service import NotificationService
        
        count = NotificationService.delete_old_notifications(db, days=30)
        
        if count > 0:
            logger.info(f"✅ 清理了 {count} 条旧通知")
        else:
            logger.debug("✅ 没有需要清理的旧通知")
        
    except Exception as e:
        logger.error(f"❌ 清理旧通知任务失败: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    try:
        check_interval = order_config.AUTO_CANCEL_CHECK_INTERVAL_MINUTES
        remind_interval = order_config.PICKUP_REMIND_CHECK_INTERVAL_MINUTES
        
        # 1. 每N分钟检查一次未支付订单（可配置超时自动取消）
        scheduler.add_job(
            func=auto_cancel_unpaid_orders,
            trigger=IntervalTrigger(minutes=check_interval),
            id='auto_cancel_unpaid_orders',
            name=f'自动取消未支付订单（每{check_interval}分钟）',
            replace_existing=True
        )
        logger.info(f"✅ 已添加定时任务：自动取消未支付订单（每{check_interval}分钟执行，超时{order_config.get_unpaid_timeout_minutes()}分钟）")
        
        # 2. 每N分钟检查一次待取餐超时订单（可配置提醒时间）
        scheduler.add_job(
            func=remind_pickup_timeout,
            trigger=IntervalTrigger(minutes=remind_interval),
            id='remind_pickup_timeout',
            name=f'待取餐超时提醒（每{remind_interval}分钟）',
            replace_existing=True
        )
        logger.info(f"✅ 已添加定时任务：待取餐超时提醒（每{remind_interval}分钟执行，超时{order_config.get_pickup_timeout_hours()}小时）")
        
        # 3. 每小时检查一次退款审批时效
        scheduler.add_job(
            func=check_refund_approvals,
            trigger=IntervalTrigger(hours=1),
            id='check_refund_approvals',
            name='检查退款审批时效（每小时）',
            replace_existing=True
        )
        logger.info("✅ 已添加定时任务：检查退款审批时效（每小时执行，24小时提醒，3天自动批准）")
        
        # 4. 每天凌晨2点清理旧通知
        from apscheduler.triggers.cron import CronTrigger
        scheduler.add_job(
            func=cleanup_old_notifications,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_old_notifications',
            name='清理旧通知（每天凌晨2点）',
            replace_existing=True
        )
        logger.info("✅ 已添加定时任务：清理旧通知（每天凌晨2点执行）")
        
        # 启动调度器
        scheduler.start()
        logger.info("=" * 60)
        logger.info("🚀 定时任务调度器已启动")
        logger.info(f"📋 配置：未支付超时={order_config.get_unpaid_timeout_minutes()}分钟，取餐超时={order_config.get_pickup_timeout_hours()}小时")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 启动定时任务调度器失败: {e}", exc_info=True)


def stop_scheduler():
    """停止定时任务调度器"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("🛑 定时任务调度器已停止")
    except Exception as e:
        logger.error(f"❌ 停止定时任务调度器失败: {e}", exc_info=True)


def get_scheduler_status():
    """获取调度器状态"""
    if not scheduler.running:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": True,
        "jobs": jobs
    }

