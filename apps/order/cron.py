from apps.order.models import OrderInfo, OrderElectron
from apps.electron.models import Electron
from datetime import datetime, timedelta
from django.db.models import F
from django.utils import timezone

def test():
    unpaid_order = OrderInfo.objects.filter(status=1)
    time_now = timezone.now()
    order_list = []
    for order in unpaid_order:
        expire_time = order.create_at + timedelta(hours=2)
        if time_now >= expire_time:
            order_list.append(order.order_id)

            electrons = OrderElectron.objects.filter(order_id=order.order_id)
            for electron in electrons:
                Electron.objects.filter(model_name=electron.eles).update(
                    platform_stock=F('platform_stock') + electron.count)

    OrderInfo.objects.filter(order_id__in=order_list).update(status=5)