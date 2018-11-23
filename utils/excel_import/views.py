from django.http import HttpResponse, JsonResponse
from rest_framework import mixins, viewsets
from django.views.generic import View
from django.utils.http import urlquote
import xlwt
import xlrd
from io import BytesIO
import json
import datetime

from apps.electron.models import ElectronKwargs, Electron, ElectronKwargsValueFront
from utils.excel_import.serializers import ExportElectronKwargsSerializers
from .form import UploadExcelForm


class ExportElectronKwargsTemplateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """导出元器件表/元器件参数表模板"""
    queryset = ElectronKwargs.objects.all()
    serializer_class = ExportElectronKwargsSerializers

    def list(self, request, *args, **kwargs):
        filename = u"元器件表数据模板"
        filename = urlquote(filename) + datetime.datetime.now().strftime("%Y%m%d%H%M") + '.xls'
        category = json.loads(request.query_params['category'])
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        electron_kwargs = ElectronKwargs.objects.filter(electron_id=int(category[-1]))
        ws = xlwt.Workbook(encoding='utf-8')
        electron_w = ws.add_sheet(u'元器件表')
        kwargs_w = ws.add_sheet(u'元器件-参数表')
        for n in range(16):
            electron_w.col(n).width = 4000
        for m in range(len(electron_kwargs) + 1):
            kwargs_w.col(m).width = 4800
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        style = xlwt.XFStyle()
        style.alignment = alignment

        # 到处元器件表模板
        electron_w.write(0, 0, '编号', style)
        electron_w.write(0, 1, '名称', style)
        electron_w.write(0, 2, '型号', style)
        electron_w.write(0, 3, '图片地址', style)
        electron_w.write(0, 4, '厂商/品牌', style)
        electron_w.write(0, 5, '来源站点', style)
        electron_w.write(0, 6, '平台价格', style)
        electron_w.write(0, 7, '库存', style)
        electron_w.write(0, 8, '特性', style)
        electron_w.write(0, 9, '描述', style)
        electron_w.write(0, 10, '数据表名', style)
        electron_w.write(0, 11, '数据表(地址)', style)
        electron_w.write(0, 12, '产地', style)
        electron_w.write(0, 13, '上市时间', style)
        electron_w.write(0, 14, '原厂链接', style)
        electron_w.write(0, 15, '联系人', style)

        electron_w.write(1, 0, 'id', style)
        electron_w.write(1, 1, 'name', style)
        electron_w.write(1, 2, 'model_name', style)
        electron_w.write(1, 3, 'images', style)
        electron_w.write(1, 4, 'factory', style)
        electron_w.write(1, 5, 'source_web', style)
        electron_w.write(1, 6, 'platform_price', style)
        electron_w.write(1, 7, 'platform_stock', style)
        electron_w.write(1, 8, 'specifc', style)
        electron_w.write(1, 9, 'desc_specific ', style)
        electron_w.write(1, 10, 'data_sheet_name', style)
        electron_w.write(1, 11, 'data_sheet', style)
        electron_w.write(1, 12, 'origin', style)
        electron_w.write(1, 13, 'market_date_at', style)
        electron_w.write(1, 14, 'factory_link', style)
        electron_w.write(1, 15, 'linkman', style)

        # 到处元器件参数表模板
        kwargs_w.write(0, 0, 'id', style)
        kwargs_w.write(1, 0, '---', style)
        col_num = 1
        for electron_kwarg in electron_kwargs:
            kwargs_w.write(0, col_num, electron_kwarg.cname, style)
            kwargs_w.write(1, col_num, electron_kwarg.id, style)
            col_num += 1

        # 写出到IO
        output = BytesIO()
        ws.save(output)
        # 重新定位到开始
        output.seek(0)
        response.write(output.getvalue())
        return response


class UploadElectronExcelView(View):
    """导入元器件和元器件参数"""

    def post(self, request):
        form = UploadExcelForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                category = json.loads(request.GET['category'])
                wb = xlrd.open_workbook(
                    filename=None, file_contents=request.FILES['excel'].read())
                # 获取上传的元器件数据表
                electron_table = wb.sheets()[0]
                electron_table_nrows = electron_table.nrows
                # 获取上传的元器件参数表
                electron_kwargs_table = wb.sheets()[1]
                electron_kwargs_table_nrows = electron_kwargs_table.nrows
                electron_kwargs_table_ncols = electron_kwargs_table.ncols
                for i in range(2, electron_table_nrows):
                    electron_col = electron_table.row_values(i)
                    if Electron.objects.filter(model_name=electron_col[2]):
                        return JsonResponse({"error:": "型号为<< %s >>的元器件已经存在, 请勿重复上传!" % electron_col[2]})
                    electron = Electron()
                    electron.category_id = int(category[-1])
                    electron.name = electron_col[1]
                    electron.model_name = electron_col[2]
                    electron.images = electron_col[3]
                    electron.factory = electron_col[4]
                    electron.source_web = electron_col[5]
                    electron.platform_price = float(electron_col[6])
                    electron.platform_stock = int(electron_col[7])
                    electron.specifc = electron_col[8]
                    electron.desc_specific = electron_col[9]
                    electron.data_sheet_name = electron_col[10]
                    electron.data_sheet = electron_col[11]
                    if '国内' == electron_col[12]:
                        electron.origin = '1'
                    elif '国外' == electron_col[12]:
                        electron.origin = '0'
                    else:
                        electron.origin = None
                    if electron_col[13]:
                        electron.market_date_at = datetime.datetime.strptime(electron_col[13], "%Y-%m-%d")
                    else:
                        electron.market_date_at = None
                    electron.factory_link = electron_col[14]
                    electron.linkman = electron_col[15]
                    electron.save()
                    try:
                        electron_kwargs_name = electron_kwargs_table.row_values(0)
                        electron_kwargs_id = electron_kwargs_table.row_values(1)
                        for j in range(2, electron_kwargs_table_nrows):
                            electron_kwargs_col = electron_kwargs_table.row_values(j)
                            if int(electron_col[0]) == int(electron_kwargs_col[0]):
                                for n in range(1, electron_kwargs_table_ncols):
                                    electron_kwargs = ElectronKwargsValueFront()
                                    electron_kwargs.electron = electron
                                    electron_kwargs.kwargs_name = electron_kwargs_name[n]
                                    electron_kwargs.kwargs_value = electron_kwargs_col[n]
                                    electron_kwargs.kwargs_id = electron_kwargs_id[n]
                                    electron_kwargs.save()
                    except Exception as e:
                        Electron.objects.filter(id=electron.id).delete()
                        return JsonResponse({"fail": "上传失败!", "error": "%s" % e.args})
                return JsonResponse({"success": "上传成功!"})
        except Exception as e:
            return JsonResponse({"fail": "上传失败!", "error": "%s" % e.args})
