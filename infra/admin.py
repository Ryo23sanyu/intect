from django.contrib import admin
from django.forms import IntegerField
from infra.models import Approach, Article, BridgePicture, DamageComment, DamageList, FullReportData, Infra, Material, NameEntry, PartsName, PartsNumber, Table, Article, LoadGrade, LoadWeight, Regulation, Rulebook, Thirdparty, UnderCondition
from django.db.models import Case, When, IntegerField
from django.db.models import F, Q
from django.db.models.functions import Cast, Substr
from django.db.models.functions import Length, Substr
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
    list_display = ('部材名', '記号', '工種', 'get_materials', '主要部材', 'display_order') # 表示するフィールド
    list_editable = ('工種', 'display_order',) # 管理画面でdisplay_orderフィールドを直接編集
    ordering = ('display_order',) # 順序フィールドで並べ替え
    def get_materials(self, obj): # 多対多フィールドの内容をカスタムメソッドで取得して文字列として返す
        return ", ".join([material.材料 for material in obj.material.all()])
    get_materials.short_description = '材料' # 管理画面での表示名を設定
admin.site.register(PartsName, PartsNameAdmin)

class PartsNumberAdmin(admin.ModelAdmin): # 番号登録
    list_display = ('infra', 'parts_name', 'symbol', 'number', 'get_material_list', 'main_frame', 'span_number', 'article') # unique_id
    ordering = ('infra', 'span_number', 'parts_name', 'number')
admin.site.register(PartsNumber, PartsNumberAdmin)

class NameEntryAdmin(admin.ModelAdmin): # 名前とアルファベットの紐付け
    list_display = ('article', 'name', 'alphabet')
admin.site.register(NameEntry, NameEntryAdmin)

class DamageListAdmin(admin.ModelAdmin): # 損傷一覧
    list_display = ('parts_name', 'number', 'damage_name', 'damage_lank', 'span_number', 'infra')
    search_fields = ('parts_name', 'infra__title', 'article__案件名') # 検索対象：「infraのtitleフィールド」と指定
    ordering = ('-span_number', '-infra')
admin.site.register(DamageList, DamageListAdmin)

class BridgePictureAdmin(admin.ModelAdmin): # 写真登録
    list_display = ('infra', 'parts_split', 'damage_name', 'picture_number', 'image', 'image_tag', 'span_number', 'article')
    search_fields = ('parts_split', 'infra__title', 'article__案件名', 'image') # 検索対象：「infraのtitleフィールド」と指定
    # 管理サイトに写真を表示する方法
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />'.format(obj.image.url))
        return "No Image"
    image_tag.short_description = 'Image'
admin.site.register(BridgePicture, BridgePictureAdmin)

# class ExcelNo10OutputAdmin(admin.ModelAdmin): # 損傷写真帳に貼付けるためのクラス
#     list_display = ('infra', 'picture_number', 'article')
#     search_fields = ('infra', 'article')
# admin.site.register(ExcelNo10Output, ExcelNo10OutputAdmin)

class FullReportDataAdmin(admin.ModelAdmin): # 損傷写真帳の全データ
    list_display = ('parts_name', 'four_numbers', 'damage_name', 'picture_number', 'span_number', 'infra', 'article')
    search_fields = ('parts_name', 'infra__title', 'article__案件名') # 検索対象：「infraのtitleフィールド」と指定
    parts_name_order = ['主桁', '横桁', '縦桁', '床版', '対傾構', '上横構', '下横構', '外ケーブル', 'ゲルバー部', 'PC定着部', '格点', 'コンクリート埋込部', 'その他', 
                        '橋脚[柱部・壁部]', '橋脚[梁部]', '橋脚[隅角部・接合部]', '橋台[胸壁]', '橋台[竪壁]', '橋台[翼壁]', '基礎[フーチング]', '基礎', 
                        '支承本体', 'アンカーボルト', '沓座モルタル', '台座コンクリート', '落橋防止システム', 
                        '高欄', '防護柵', '地覆', '中央分離帯', '伸縮装置', '遮音施設', '照明施設', '縁石', '舗装', '排水ます', '排水管', '点検施設', '添架物', '袖擁壁']
    damage_name_order = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳', '㉑', '㉒', '㉓', '㉔', '㉕', '㉖']

    def get_ordering(self, request):
        return []  # デフォルトではカスタムロジックで並び替えるため空に

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # parts_nameの部分一致並び替え用ケース文
        parts_name_cases = [When(parts_name__icontains=pn, then=idx) for idx, pn in enumerate(self.parts_name_order)]
        damage_name_cases = [When(damage_name__icontains=dn, then=idx) for idx, dn in enumerate(self.damage_name_order)]

        # span_number の長さを取得し、それを使って数値部分を抽出
        qs = qs.annotate(
            span_length=Length('span_number'),
            parts_order=Case(*parts_name_cases, output_field=IntegerField(), default=len(self.parts_name_order)),
            damage_order=Case(*damage_name_cases, output_field=IntegerField(), default=len(self.damage_name_order))
        )

        # Cast & Substr を使って span_number の数値部分を抽出
        qs = qs.annotate(
            span_number_numeric=Cast(Substr('span_number', 1, F('span_length') - 2), IntegerField())
        )

        qs = qs.order_by('article__案件名', 'infra__title', 'span_number_numeric', 'parts_order', 'four_numbers', 'picture_number', 'damage_order')
        return qs

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        exact_match_query = Q(infra__title=search_term)
        queryset = queryset.filter(exact_match_query | Q(parts_name__icontains=search_term) | Q(article__案件名__icontains=search_term))
        return queryset, use_distinct
    
admin.site.register(FullReportData, FullReportDataAdmin)

""" 管理サイトの並び替え表示に必要な動作 """
class CustomPartsNameFilter(admin.SimpleListFilter):
    title = 'Parts Name'
    parameter_name = 'replace_name'

    def lookups(self, request, model_admin):
        return [
            ('主桁', '主桁'),
            ('横桁', '横桁'),
            ('縦桁', '縦桁'),
            ('床版', '床版'),
            ('対傾構', '対傾構'),
            ('上横構', '上横構'),
            ('下横構', '下横構'), 
            ('アーチリブ', 'アーチリブ'),
            ('補剛桁', '補剛桁'),
            ('吊り材', '吊り材'),
            ('支柱', '支柱'),
            ('橋門構', '橋門構'),
            ('外ケーブル', '外ケーブル'),
            ('ゲルバー部', 'ゲルバー部'),
            ('PC定着部', 'PC定着部'),
            ('格点', '格点'),
            ('コンクリート埋込部', 'コンクリート埋込部'),
            ('その他', 'その他'),
            ('橋脚[柱部・壁部]', '橋脚[柱部・壁部]'),
            ('橋脚[梁部]', '橋脚[梁部]'),
            ('橋脚[隅角部・接合部]', '橋脚[隅角部・接合部]'),
            ('橋台[胸壁]', '橋台[胸壁]'),
            ('橋台[竪壁]', '橋台[竪壁]'),
            ('橋台[翼壁]', '橋台[翼壁]'),
            ('基礎[フーチング]', '基礎[フーチング]'),
            ('基礎', '基礎'),
            ('支承本体', '支承本体'),
            ('アンカーボルト', 'アンカーボルト'),
            ('沓座モルタル', '沓座モルタル'),
            ('台座コンクリート', '台座コンクリート'),
            ('落橋防止システム', '落橋防止システム'),
            ('高欄', '高欄'),
            ('防護柵', '防護柵'),
            ('地覆', '地覆'),
            ('中央分離帯', '中央分離帯'),
            ('伸縮装置', '伸縮装置'),
            ('遮音施設', '遮音施設'),
            ('照明施設', '照明施設'),
            ('縁石', '縁石'),
            ('舗装', '舗装'),
            ('排水ます', '排水ます'),
            ('排水管', '排水管'),
            ('点検施設', '点検施設'),
            ('添架物', '添架物'),
            ('袖擁壁', '袖擁壁')
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(replace_name__icontains=self.value())
        return queryset

class DamageCommentAdmin(admin.ModelAdmin): # 所見データ
    list_display = ('parts_name', 'parts_number', 'damage_name', 'number', 'infra', 'span_number', 'article')
    list_filter = (CustomPartsNameFilter,)
    search_fields = ('replace_name__icontains', 'infra__title', 'article__案件名')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            parts_order=Case(
                When(replace_name='主桁', then=0),
                When(replace_name='横桁', then=1),
                When(replace_name='床版', then=2),
                When(replace_name='排水管', then=3),
                default=4,
                output_field=IntegerField(),
            )
        ).order_by('span_number', 'replace_name', 'parts_number', 'number')
                  #   1(径間)          主桁　　　　　　　01　　　　　1(腐食)
admin.site.register(DamageComment, DamageCommentAdmin)