from fastapi import APIRouter

# 显式导入所有路由模块，确保 PyInstaller 能正确打包
# 注意：不能使用 from app.api.v1 import，会导致循环导入
# 直接导入模块文件即可
import app.api.v1.auth as auth
import app.api.v1.users as users
import app.api.v1.canteens as canteens
import app.api.v1.dishes as dishes
import app.api.v1.orders as orders
import app.api.v1.media as media
import app.api.v1.location as location
import app.api.v1.address as address
import app.api.v1.favorite as favorite
import app.api.v1.review as review
import app.api.v1.cart as cart
import app.api.v1.message as message
import app.api.v1.window as window
import app.api.v1.coupon as coupon
import app.api.v1.statistics as statistics
import app.api.v1.notification as notification
import app.api.v1.refund as refund
import app.api.v1.canteen_review as canteen_review
import app.api.v1.export as export
import app.api.v1.activity as activity
import app.api.v1.faq as faq
import app.api.v1.search as search
import app.api.v1.browse as browse
import app.api.v1.websocket as websocket

router = APIRouter()

__all__ = [
    'auth',
    'users',
    'canteens',
    'dishes',
    'orders',
    'media',
    'location',
    'address',
    'favorite',
    'review',
    'cart',
    'message',
    'window',
    'coupon',
    'statistics',
    'notification',
    'refund',
    'canteen_review',
    'export',
    'activity',
    'faq',
    'search',
    'browse',
    'websocket',
]
