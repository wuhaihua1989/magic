from django.contrib import admin
from apps.product.models import *

# Register your models here.
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(ProductVideo)
admin.site.register(ProductElectron)
admin.site.register(CustomProduct)
admin.site.register(CustomProductElectron)
admin.site.register(CustomProductScheme)