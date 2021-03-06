# Generated by Django 2.0.7 on 2018-11-23 05:55

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('files', models.FileField(blank=True, null=True, upload_to='files', verbose_name='files_set')),
            ],
            options={
                'verbose_name': '文件集',
                'verbose_name_plural': '文件集',
                'db_table': 'm_db_files',
            },
        ),
        migrations.CreateModel(
            name='FreightCarrier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_money', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='最大金额')),
                ('is_gd', models.BooleanField(default=False, verbose_name='是否是广东地区')),
                ('gd_freight', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='同城费用')),
                ('another_freight', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='异地费用')),
            ],
            options={
                'verbose_name': '运费计价规则',
                'verbose_name_plural': '运费计价规则',
                'db_table': 'm_freight_carrier',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images', verbose_name='image_set')),
            ],
            options={
                'verbose_name': '图集',
                'verbose_name_plural': '图集',
                'db_table': 'm_db_img',
            },
        ),
        migrations.CreateModel(
            name='LeaveMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('update_at', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=88, verbose_name='留言人姓名')),
                ('email', models.EmailField(max_length=188, verbose_name='留言人email')),
                ('content', models.TextField(verbose_name='留言内容')),
            ],
            options={
                'verbose_name': '建议或意见留言',
                'verbose_name_plural': '建议或意见留言',
                'db_table': 'm_leave_message',
            },
        ),
        migrations.CreateModel(
            name='MagicContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('update_at', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('title', models.CharField(blank=True, max_length=266, null=True, verbose_name='标题')),
                ('content', models.TextField(blank=True, null=True, verbose_name='填充内容')),
                ('enable', models.BooleanField(default=False, verbose_name='是否启用')),
            ],
            options={
                'verbose_name': '内容',
                'verbose_name_plural': '内容',
                'db_table': 'm_magic_content',
            },
        ),
        migrations.CreateModel(
            name='MagicContentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(max_length=166, verbose_name='内容分类')),
                ('icon', models.CharField(blank=True, max_length=512, null=True, verbose_name='图片')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='config.MagicContentCategory')),
            ],
            options={
                'verbose_name': '内容类型',
                'verbose_name_plural': '内容类型',
                'db_table': 'm_magic_content_category',
            },
        ),
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('update_at', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('context', models.TextField(blank=True, null=True, verbose_name='协议内容')),
            ],
            options={
                'verbose_name': '网站协议',
                'verbose_name_plural': '网站协议',
                'db_table': 'm_protocol',
            },
        ),
        migrations.CreateModel(
            name='SEO',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('update_at', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('title', models.CharField(blank=True, max_length=266, null=True, verbose_name='标题')),
                ('key', models.CharField(blank=True, max_length=266, null=True, verbose_name='关键字')),
                ('description', models.TextField(blank=True, null=True, verbose_name='描述')),
            ],
            options={
                'verbose_name': 'SEO信息',
                'verbose_name_plural': 'SEO信息',
                'db_table': 'm_seo',
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('videos', models.FileField(blank=True, null=True, upload_to='videos', verbose_name='video_set')),
            ],
            options={
                'verbose_name': '视频集',
                'verbose_name_plural': '视频集',
                'db_table': 'm_db_videos',
            },
        ),
        migrations.CreateModel(
            name='WebSite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='创建时间')),
                ('update_at', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('company', models.CharField(blank=True, max_length=188, null=True, verbose_name='公司名称')),
                ('industry', models.CharField(blank=True, max_length=188, null=True, verbose_name='行业类别')),
                ('tel_man', models.CharField(blank=True, max_length=188, null=True, verbose_name='联系人')),
                ('mail_code', models.CharField(blank=True, max_length=166, null=True, verbose_name='邮编')),
                ('four_tel_number', models.CharField(blank=True, max_length=166, null=True, verbose_name='400电话')),
                ('fax', models.CharField(blank=True, max_length=166, null=True, verbose_name='传真')),
                ('email', models.EmailField(blank=True, max_length=166, null=True, verbose_name='邮箱')),
                ('tel_number', models.CharField(blank=True, max_length=166, null=True, verbose_name='座机')),
                ('qq', models.CharField(blank=True, max_length=166, null=True, verbose_name='客服QQ')),
                ('address', models.CharField(blank=True, max_length=266, null=True, verbose_name='联系地址')),
                ('web_site', models.CharField(blank=True, max_length=188, null=True, verbose_name='公司网站')),
                ('logo', models.TextField(blank=True, null=True, verbose_name='logo')),
                ('source', models.TextField(blank=True, null=True, verbose_name='图片')),
                ('description', models.TextField(blank=True, null=True, verbose_name='公司描述')),
            ],
            options={
                'verbose_name': '网站',
                'verbose_name_plural': '网站',
                'db_table': 'm_website',
            },
        ),
        migrations.AddField(
            model_name='magiccontent',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='config.MagicContentCategory', verbose_name='类型'),
        ),
    ]
