from django.db import models
from datetime import datetime

class BaseModel(models.Model):
    create_at = models.DateTimeField(default=datetime.now,verbose_name="创建时间")
    update_at= models.DateField(auto_now=True,verbose_name="更新时间")

    class Meta:
        abstract = True