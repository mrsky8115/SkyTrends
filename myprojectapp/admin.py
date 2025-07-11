from django.contrib import admin
from .models import product, cart, orders,ShippingDetail
 
# Register your models here.
class ProdAdmin(admin.ModelAdmin):
    list_display=['id','name','original_price','price','pdetails','type','size','cat','is_active']
    list_filter=('cat','is_active')
class cartAdmin(admin.ModelAdmin):
    list_display=['id','uid','pid']


class orderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'tracking_id', 'shipping_address', 'current_status', 'uid', 'pid', 'last_updated')
    search_fields = ('order_id', 'tracking_id')

class ShippingDetailAdmin(admin.ModelAdmin):
    list_display = ('user','full_name','phone','address')


admin.site.register(cart, cartAdmin)
admin.site.register(product, ProdAdmin)
admin.site.register(orders, orderAdmin)
admin.site.register(ShippingDetail,ShippingDetailAdmin)

admin.site.site_header = "Sky Trends"
admin.site.site_title = "Aakash Vishwakarma"