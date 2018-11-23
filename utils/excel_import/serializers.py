from rest_framework import serializers
from apps.electron.models import ElectronKwargs


class ExportElectronKwargsSerializers(serializers.ModelSerializer):
    class Meta:
        model = ElectronKwargs
        fields = ['electron', 'cname']

