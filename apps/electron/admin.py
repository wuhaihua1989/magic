from django.contrib import admin
from apps.electron.models import *

admin.site.register(Electron)
admin.site.register(ElectronCategory)
admin.site.register(Supplier)
admin.site.register(ElectronSupplier)
admin.site.register(ElectronKwargs)
admin.site.register(ElectronCircuitDiagram)
admin.site.register(ElectronVideo)
admin.site.register(ElectronConsumer)
admin.site.register(PinToPin)
