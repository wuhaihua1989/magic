from django import forms
from apps.product.validationerror import ValidationError


def validate_excel(value):
    if value.name.split('.')[-1] not in ['xls', 'xlsx']:
        raise ValidationError({'error': '上传的文件格式错误,只能上传xls或xlsx,上传的错误格式为:%s' % value.name.split('.')[-1]})


class UploadExcelForm(forms.Form):
    excel = forms.FileField(validators=[validate_excel])
