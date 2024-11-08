from django.contrib import admin
from infra.models import Approach, Article, BridgePicture, DamageList, Infra, Material, NameEntry, PartsName, PartsNumber, Table, Article, LoadGrade, LoadWeight, Regulation, Rulebook, Thirdparty, UnderCondition
from django.utils.html import format_html

class ArticleAdmin(admin.ModelAdmin): # 案件
    list_display = ('案件名', '土木事務所', '対象数', 'その他')
admin.site.register(Article, ArticleAdmin)

class InfraAdmin(admin.ModelAdmin): # 橋梁
    list_display = ('title', '径間数', '路線名', 'article')
admin.site.register(Infra, InfraAdmin)

admin.site.register(Regulation)     # 道路規制
admin.site.register(LoadWeight)     # 活荷重
admin.site.register(LoadGrade)      # 等級
admin.site.register(Rulebook)       # 適用示方書
admin.site.register(Approach)       # 近接方法
admin.site.register(Thirdparty)     # 第三者点検の有無
admin.site.register(UnderCondition) # 路下条件
admin.site.register(Material)       # 番号登録(材料)

class TableAdmin(admin.ModelAdmin): # 損傷写真帳
    list_display = ('infra', 'article', 'dxf')
admin.site.register(Table, TableAdmin)

class PartsNameAdmin(admin.ModelAdmin): # 部材名登録
    list_display = ('部材名', '記号', 'get_materials', '主要部材', 'display_order') # 表示するフィールド
    list_editable = ('display_order',) # 管理画面でdisplay_orderフィールドを直接編集
    ordering = ('display_order',) # 順序フィールドで並べ替え
    def get_materials(self, obj): # 多対多フィールドの内容をカスタムメソッドで取得して文字列として返す
        return ", ".join([material.材料 for material in obj.material.all()])
    get_materials.short_description = '材料' # 管理画面での表示名を設定
admin.site.register(PartsName, PartsNameAdmin)

class PartsNumberAdmin(admin.ModelAdmin): # 番号登録
    list_display = ('infra', 'parts_name', 'symbol', 'number', 'get_material_list', 'main_frame', 'span_number', 'article', 'unique_id')
    ordering = ('infra', 'span_number', 'parts_name', 'number')
admin.site.register(PartsNumber, PartsNumberAdmin)

class NameEntryAdmin(admin.ModelAdmin): # 名前とアルファベットの紐付け
    list_display = ('article', 'name', 'alphabet')
admin.site.register(NameEntry, NameEntryAdmin)

class DamageListAdmin(admin.ModelAdmin): # 損傷一覧
    list_display = ('parts_name', 'number', 'damage_name', 'damage_lank', 'span_number', 'infra')
    ordering = ('-span_number', '-infra')
admin.site.register(DamageList, DamageListAdmin)

class BridgePictureAdmin(admin.ModelAdmin): # 写真登録
    list_display = ('infra', 'parts_split', 'damage_name', 'picture_number', 'image', 'image_tag', 'span_number', 'article')
    # 管理サイトに写真を表示する方法
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />'.format(obj.image.url))
        return "No Image"
    image_tag.short_description = 'Image'
admin.site.register(BridgePicture, BridgePictureAdmin)