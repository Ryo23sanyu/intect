# << 案件登録フォーム >>
from django import forms
from .models import Article, BridgePicture, DamageComment, FullReportData, Infra, NameEntry, PartsNumber, Table
from django.core.exceptions import ValidationError

# << 案件登録フォーム >>
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['案件名', '土木事務所', '対象数', '担当者名', 'その他']
        
# << 橋梁登録フォーム >>
class InfraForm(forms.ModelForm):
    class Meta:
        model = Infra
        fields = ['title', '径間数', '橋長', '全幅員', '路線名', 'latitude', 'longitude', 'end_latitude', 'end_longitude', '橋梁コード', '活荷重', '等級', '適用示方書', 
                  '上部構造形式', '下部構造形式', '基礎構造形式', '近接方法', '交通規制', '第三者点検', '海岸線との距離', '路下条件', 
                  '特記事項', 'カテゴリー', '交通量', '大型車混入率', 'article']

# << 橋梁データ・作成フォーム >>
class BridgeCreateForm(forms.ModelForm):
    class Meta:
        model = Infra
        fields = ['交通規制', '活荷重', '等級', '適用示方書', '近接方法', '第三者点検', '路下条件'] # 他のフィールドについても必要に応じて追加してください。
        widgets = {
            '交通規制': forms.CheckboxSelectMultiple,
            '活荷重': forms.RadioSelect,
            '等級': forms.RadioSelect,
            '適用示方書': forms.RadioSelect,
            '近接方法': forms.CheckboxSelectMultiple,
            '第三者点検': forms.RadioSelect,
            '路下条件': forms.CheckboxSelectMultiple,
        }
        
# << 橋梁データ・更新フォーム >>
class BridgeUpdateForm(forms.ModelForm):
    class Meta:
        model = Infra
        fields = ['交通規制', '活荷重', '等級', '適用示方書', '近接方法', '第三者点検', '路下条件'] # 他のフィールドについても必要に応じて追加してください。
        widgets = {
            '交通規制': forms.CheckboxSelectMultiple,
            '活荷重': forms.RadioSelect,
            '等級': forms.RadioSelect,
            '適用示方書': forms.RadioSelect,
            '近接方法': forms.CheckboxSelectMultiple,
            '第三者点検': forms.RadioSelect,
            '路下条件': forms.CheckboxSelectMultiple,
        }
        
# << dxfファイルの登録フォーム >>
class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['infra', 'dxf', 'article']
        
# << 名前とアルファベットの登録 >>
class NameEntryForm(forms.ModelForm):
    class Meta:
        model = NameEntry
        fields = ['name', 'alphabet', 'article']

# << 要素番号の登録 >>
class PartsNumberForm(forms.ModelForm):
    class Meta:
        model = PartsNumber
        fields = ['parts_name', 'symbol', 'material', 'main_frame', 'span_number', 'number', 'infra', 'article']
        
    def clean(self):
        data = self.cleaned_data
        print(data)

        materials = data["material"]

        #タグは3個まで
        if len(materials) > 3:
            raise ValidationError("materialは3個まで")

        return self.cleaned_data
    
   
# << 写真帳の全データを管理サイトに登録 >>
class FullReportDataForm(forms.ModelForm):
    class Meta:
        model = FullReportData
        fields = ['parts_name', 'damage_name', 'join', 'picture_number', 'this_time_picture', 'last_time_picture',
                  'textarea_content', 'damage_coordinate_x', 'damage_coordinate_y', 'picture_coordinate_x', 'picture_coordinate_y']

# << 損傷写真帳の入力データを登録 >>　update_full_report_data関数をビューに作成　update_full_report_dataパスをURLに作成
class FullReportDataEditForm(forms.ModelForm):
    class Meta:
        model = FullReportData
        fields = ["measurement", "damage_size", "classification", "pattern"]

# << 損傷写真帳の変更内容を保存 >>
class EditReportDataForm(forms.ModelForm):
    class Meta:
        model = FullReportData
        fields = ['parts_name', 'damage_name']
        
class BridgePictureForm(forms.ModelForm):
    class Meta:
        model = BridgePicture
        fields = ['image', 'picture_number', 'damage_name', 'parts_split', 'memo', 'damage_coordinate_x', 'damage_coordinate_y', 'picture_coordinate_x', 'picture_coordinate_y', 'span_number', 'table', 'infra', 'article']

# << 所見のコメントを登録 >>
class DamageCommentEditForm(forms.ModelForm):
    class Meta:
        model = DamageComment # モデルのクラス名
        fields = ["comment"] # モデルのフィールド名
        
# << 判定区分のボタンを登録 >>
class DamageCommentJadgementEditForm(forms.ModelForm):
    class Meta:
        model = DamageComment
        fields = ["jadgement"]
        
# << 損傷原因のボタンを登録 >>
class DamageCommentCauseEditForm(forms.ModelForm):
    class Meta:
        model = DamageComment
        fields = ["cause"]