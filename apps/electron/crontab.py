from datetime import datetime
from apps.electron.models import Electron, ElectronCategory, ElectronKwargsValueFront, PinToPin, SimilarElectron
from apps.electron.models import PinToPinIsDelete, SimilarElectronIsDelete


def add_pin_or_similar_electron():
    print('-----------------------------------------------------------------')
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("程序执行开始时间：%s" % start_time)
    electrons_category = ElectronCategory.objects.filter(children=None)
    for electron_category in electrons_category:
        original_electrons = Electron.objects.filter(category=electron_category, isDelete=False)
        replace_electrons = Electron.objects.filter(category=electron_category, isDelete=False)
        for original_electron in original_electrons:

            original_pin_kwargs = ElectronKwargsValueFront.objects.filter(
                electron=original_electron,
                kwargs__electron=electron_category
            )
            if original_pin_kwargs.count() != 0:
                for replace_electron in replace_electrons:
                    if original_electron.model_name != replace_electron.model_name:
                        pin_to_pin_count = PinToPin.objects.filter(
                            electron=original_electron,
                            pin_to_pin=replace_electron
                        ).count()
                        pin_to_pin_delete_count = PinToPinIsDelete.objects.filter(
                            electron_id=original_electron.id,
                            pin_to_pin_id=replace_electron.id
                        ).count()
                        if not pin_to_pin_count and not pin_to_pin_delete_count:
                            replace_pin_kwargs = ElectronKwargsValueFront.objects.filter(
                                electron=replace_electron,
                                kwargs__electron=electron_category
                            )
                            if len(original_pin_kwargs) == len(replace_pin_kwargs):
                                replace_pin_kwarg_nums = 0
                                for original_kwarg in original_pin_kwargs:
                                    for replace_kwarg in replace_pin_kwargs:
                                        if original_kwarg.kwargs_name == replace_kwarg.kwargs_name \
                                                and original_kwarg.kwargs_value == replace_kwarg.kwargs_value:
                                            replace_pin_kwarg_nums += 1
                                if len(original_pin_kwargs) == replace_pin_kwarg_nums:
                                    pin_to_pin_electron = PinToPin()
                                    pin_to_pin_electron.electron = original_electron
                                    pin_to_pin_electron.pin_to_pin = replace_electron
                                    pin_to_pin_electron.save()
                                    print("元器件为：%s, 添加的PinToPin元器件为：%s" % (original_electron.model_name,
                                                                           replace_electron.model_name))

            original_similar_kwargs = ElectronKwargsValueFront.objects.filter(
                electron=original_electron,
                kwargs__electron=electron_category,
                kwargs__is_contrast=True
            )
            if original_similar_kwargs.count() != 0:
                for replace_electron in replace_electrons:
                    if original_electron.model_name != replace_electron.model_name:
                        similar_count = SimilarElectron.objects.filter(
                            electron=original_electron,
                            similar_electron=replace_electron
                        ).count()
                        similar_delete_count = SimilarElectronIsDelete.objects.filter(
                            electron_id=original_electron.id,
                            similar_id=replace_electron.id
                        ).count()
                        if not similar_count and not similar_delete_count:
                            replace_similar_kwargs = ElectronKwargsValueFront.objects.filter(
                                electron=replace_electron,
                                kwargs__electron=electron_category,
                                kwargs__is_contrast=True
                            )
                            if len(original_similar_kwargs) <= len(replace_similar_kwargs):
                                replace_similar_kwarg_nums = 0
                                for original_kwarg in original_similar_kwargs:
                                    for replace_kwarg in replace_similar_kwargs:
                                        if original_kwarg.kwargs_name == replace_kwarg.kwargs_name \
                                                and original_kwarg.kwargs_value == replace_kwarg.kwargs_value:
                                            replace_similar_kwarg_nums += 1
                                if len(original_similar_kwargs) == replace_similar_kwarg_nums:
                                    similar_electron = SimilarElectron()
                                    similar_electron.electron = original_electron
                                    similar_electron.similar = replace_electron
                                    similar_electron.save()
                                    print("元器件为：%s, 添加的可替代元器件为：%s" % (original_electron.model_name,
                                                                      replace_electron.model_name))
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("程序执行结束时间：%s" % end_time)
    print('*****************************************************************')
