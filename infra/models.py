import re
import uuid
from django.db import models
from django.core.validators import RegexValidator

# << 案件登録 >>
CATEGORY = (('bridge', '橋梁'), ('pedestrian', '歩道橋'), ('other', 'その他'))
class Article(models.Model):
    案件名 = models.CharField(max_length=100)
    土木事務所 = models.CharField(max_length=100)
    対象数 = models.IntegerField()
    担当者名 = models.CharField(max_length=100)
    その他 = models.CharField(max_length=100)
    def __str__(self):
        return self.案件名

# << 橋梁緒言 >>
交通規制_CHOICES = (('無し', '無し'),('片側交互通行', '片側交互通行'),('車線減少', '車線減少'),('歩道規制', '歩道規制'),('通行止め', '通行止め'))
class Regulation(models.Model):
    交通規制 = models.CharField(max_length=50, choices=交通規制_CHOICES)
    def __str__(self):
        return self.交通規制
活荷重_CHOICES = (('不明', '不明'),('A活荷重', 'A活荷重'),('B活荷重', 'B活荷重'),('TL-20', 'TL-20'),('TL-14', 'TL-14'),('TL-6', 'TL-6'))
class LoadWeight(models.Model):
    活荷重 = models.CharField(max_length=50, choices=活荷重_CHOICES)
    def __str__(self):
        return self.活荷重
等級_CHOICES = (('不明', '不明'),('一等橋', '一等橋'),('二等橋', '二等橋'),('三等橋', '三等橋'),('その他', 'その他'))
class LoadGrade(models.Model):
    等級 = models.CharField(max_length=50, choices=等級_CHOICES)
    def __str__(self):
        return self.等級
適用示方書_CHOICES = (('不明', '不明'),('平成29年 道路橋示方書', '平成29年 道路橋示方書'),('平成24年 道路橋示方書', '平成24年 道路橋示方書'),('平成14年 道路橋示方書', '平成14年 道路橋示方書'),('平成8年 道路橋示方書', '平成8年 道路橋示方書'),('平成5年 道路橋示方書', '平成5年 道路橋示方書'),('平成2年 道路橋示方書', '平成2年 道路橋示方書'),\
    ('昭和55年 道路橋示方書', '昭和55年 道路橋示方書'),('昭和53年 道路橋示方書', '昭和53年 道路橋示方書'),('昭和47年 道路橋示方書', '昭和47年 道路橋示方書'),('昭和43年 プレストレスコンクリート道路橋示方書', '昭和43年 プレストレスコンクリート道路橋示方書'),\
        ('昭和39年 鉄筋コンクリート道路橋示方書', '昭和39年 鉄筋コンクリート道路橋示方書'),('昭和31年 鋼道路橋設計示方書', '昭和31年 鋼道路橋設計示方書'),('昭和15年 鋼道路橋設計示方書案', '昭和15年 鋼道路橋設計示方書案'),('大正15年 道路構造に関する細則案', '大正15年 道路構造に関する細則案'))
class Rulebook(models.Model):
    適用示方書 = models.CharField(max_length=100, choices=適用示方書_CHOICES)
    def __str__(self):
        return self.適用示方書
近接方法_CHOICES = (('地上', '地上'),('梯子', '梯子'),('橋梁点検車', '橋梁点検車'),('高所作業車', '高所作業車'),('軌陸車', '軌陸車'),('ボート', 'ボート'),('ロープアクセス', 'ロープアクセス'),('ドローン', 'ドローン'),('ファイバースコープ', 'ファイバースコープ'),('画像解析', '画像解析'))
class Approach(models.Model):
    近接方法 = models.CharField(max_length=50,choices=近接方法_CHOICES)
    def __str__(self):
        return self.近接方法
第三者点検_CHOICES = (('有り', '有り'),('無し', '無し'))
class Thirdparty(models.Model):
    第三者点検 = models.CharField(max_length=50, choices=第三者点検_CHOICES)
    def __str__(self):
        return self.第三者点検
路下条件_CHOICES = (('河川', '河川'),('水路', '水路'),('湖沼', '湖沼'),('海洋', '海洋'),('道路', '道路'),('鉄道', '鉄道'))
class UnderCondition(models.Model):
    路下条件 = models.CharField(max_length=50, choices=路下条件_CHOICES)
    def __str__(self):
        return self.路下条件

# << 橋梁登録 >>
class Infra(models.Model):
    title = models.CharField(max_length=100)# 橋名
    径間数 = models.IntegerField()# 径間数
    橋長 = models.DecimalField(max_digits=10, decimal_places=2)# 橋長(最大桁数10桁、小数点以下2桁)
    全幅員 = models.DecimalField(max_digits=10, decimal_places=2)# 全幅員(最大桁数10桁、小数点以下2桁)
    路線名 = models.CharField(max_length=200)# 路線名
    latitude = models.CharField(max_length=50, blank=True)# 起点側緯度
    longitude = models.CharField(max_length=50, blank=True)# 起点側経度
    end_latitude = models.CharField(max_length=50, blank=True)# 終点側緯度
    end_longitude = models.CharField(max_length=50, blank=True)# 終点側経度
    橋梁コード = models.CharField(max_length=50, blank=True)# 橋梁コード
    活荷重 = models.ManyToManyField(LoadWeight)# 活荷重
    等級 = models.ManyToManyField(LoadGrade)# 等級
    適用示方書 = models.ManyToManyField(Rulebook)# 適用示方書
    上部構造形式 = models.CharField(max_length=100)# 上部構造形式
    下部構造形式 = models.CharField(max_length=100)# 下部構造形式
    基礎構造形式 = models.CharField(max_length=100)# 基礎構造形式
    近接方法 = models.ManyToManyField(Approach)# 近接方法
    交通規制 = models.ManyToManyField(Regulation)# 交通規制
    第三者点検 = models.ManyToManyField(Thirdparty)# 第三者点検の有無
    海岸線との距離 = models.CharField(max_length=100)# 海岸線の距離
    路下条件 = models.ManyToManyField(UnderCondition)# 路下条件
    特記事項 = models.CharField(max_length=100, blank=True)# 特記事項
    カテゴリー = models.CharField(max_length=100, choices = CATEGORY)# カテゴリー
    交通量 = models.CharField(max_length=10, blank=True)# 12時間交通量
    大型車混入率 = models.CharField(max_length=10, blank=True)# 大型車混入率
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    def __str__(self):
        return self.title
      
# << dxfファイル登録 >>
class Table(models.Model):
    infra = models.ForeignKey(Infra, verbose_name="橋梁名", on_delete=models.CASCADE) # ForeignKeyフィールドによってInfraとのリレーションシップを定義
    dxf = models.FileField(verbose_name="dxfファイル", upload_to="infra/table/dxf/")
    article = models.ForeignKey(Article, verbose_name="案件名", on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.infra}：{self.article}（{self.dxf}）"
    
# << 名前とアルファベットの登録 >>
class NameEntry(models.Model):
    name = models.CharField(max_length=50)
    alphabet_regex = RegexValidator(regex=r"[A-Za-z]+")
    alphabet = models.CharField(max_length=50, validators=[alphabet_regex])
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    
    # 文字列表現を返すために使用
    def __str__(self):
        return f"{self.article} {self.name} ({self.alphabet})" # 例：佐藤(S)
    
# << 部材の材料 >>
材料_CHOICES = (('鋼', '鋼'),('コンクリート', 'コンクリート'),('ゴム', 'ゴム'),('アスファルト', 'アスファルト'),('塩ビ', '塩ビ'),('その他', 'その他'))
class Material(models.Model):
    材料 = models.CharField(max_length=100, choices=材料_CHOICES)
    def __str__(self):
        return self.材料
    
# << 要素番号の登録 >>
工種_CHOICES = (('上部構造', '上部構造'),('下部構造', '下部構造'),('カルバート', 'カルバート'),('支承部', '支承部'),('路上', '路上'),('排水施設', '排水施設'),('その他', 'その他'))
class PartsName(models.Model):
    部材名 = models.CharField(max_length=255)
    記号 = models.CharField(max_length=50)
    主要部材 = models.BooleanField()
    工種 = models.CharField(max_length=100, choices=工種_CHOICES, null=True, blank=True)
    material = models.ManyToManyField(Material) # 多対多のリレーションに必要
    display_order = models.PositiveIntegerField(default=0) # 順番設定用
    class Meta:
        ordering = ['display_order']
        
    def __str__(self):
        return self.部材名

# << 登録した要素番号を1つずつDBに登録 >>
class PartsNumber(models.Model):
    parts_name = models.ForeignKey(PartsName, verbose_name="部材名", on_delete=models.CASCADE) # 多対多のリレーションに必要
    # 4040 もしくは 2020~4030 2パターンだけを許可する正規表現のバリデーションを作る
    # 4桁 と 4桁~4桁 を許す正規表現　　　　　　　 　　↓ もしくは
    number_regex = RegexValidator(regex=r"(^\d{4}$)|(^\d{4}~\d{4}$)")
    #                            最初の文字 ↑     ↑ 最後の文字
    #                                            ↓ 追加のバリデーションをする、フィールドオプション
    number = models.CharField(max_length=50, validators=[number_regex])
    symbol = models.CharField(max_length=100)
    material = models.ManyToManyField(Material)
    main_frame = models.BooleanField()
    #Infraと1対多のリレーションを組む。
    span_number = models.CharField(max_length=50)
    infra = models.ForeignKey(Infra, verbose_name="Infra", on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) # ユニークIDを設定するためのフィールド(UUID)
    class Meta:
        # ユニークの設定(fieldsの組み合わせを一意とする。nullが許可されているとデータが重複する可能性があるため、notnullの要素を扱う)
        constraints = [
            models.UniqueConstraint(fields=['parts_name', 'number', 'span_number', 'infra'], name='unique_parts_number')
        ]
    def __str__(self):
        materials_list = ", ".join([str(material) for material in self.material.all()])
        return f"{self.infra}{self.parts_name}({self.symbol}{self.number}):{materials_list}/{self.main_frame}:{self.span_number}径間"
    # adminに材料を表示できるようにget_material_listを作成
    def get_material_list(self):
        return ", ".join([m.材料 for m in self.material.all()])

    get_material_list.short_description = "Material"
    
# << 写真データをDBに登録（FullReportDataクラスと紐付けて表示） >>
class BridgePicture(models.Model):
    image = models.ImageField(upload_to='photos/') # 写真データ
    picture_number = models.IntegerField(null=True, blank=True) # 数字のみの入力
    picture_count = models.TextField(null=True, blank=True)# models.TextField()：文字数上限なし
    damage_name = models.CharField(max_length=255) # '①腐食(大大)-e', '⑤防食機能の劣化(分類1)-e'
    parts_split = models.CharField(max_length=255) # '排水管 Dp00'
    damage_coordinate_x = models.CharField(max_length=255) # '538482.3557216563', '229268.8593029478'
    damage_coordinate_y = models.CharField(max_length=255) # '538482.3557216563', '229268.8593029478'
    memo = models.TextField()# models.TextField()：文字数上限なし
    picture_coordinate_x = models.CharField(max_length=255, null=True, blank=True) # '538810.3087944178', '228910.3502713814'
    picture_coordinate_y = models.CharField(max_length=255, null=True, blank=True) # '538810.3087944178', '228910.3502713814'
    span_number = models.CharField(max_length=255) # 1径間
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE) # 一意にするためのarticle
    infra = models.ForeignKey(Infra, verbose_name="橋梁名", on_delete=models.CASCADE) # 一意にするためのinfra
    class Meta:
        # ユニークの設定(fieldsの組み合わせを一意とする。nullが許可されているとデータが重複する可能性があるため、notnullの要素を扱う)
        constraints = [
            models.UniqueConstraint(fields=['image', 'damage_coordinate_x', 'damage_coordinate_y', 'span_number', 'table', 'infra', 'article'], name='unique_bridge_picture')
        ]

# << 損傷用のデータをDBに登録 >>
class FullReportData(models.Model):
    parts_name = models.CharField(max_length=255) # '排水管 Dp0101'
    damage_name = models.CharField(max_length=255) # '①腐食(大大)-e', '⑤防食機能の劣化(分類1)-e'
    parts_split = models.CharField(max_length=255) # '排水管 Dp00'
    four_numbers = models.CharField(max_length=255) # '0101'
    join = models.CharField(max_length=255) # {'parts_name': ['排水管 Dp0101'], 'damage_name': ['①腐食(大大)-e', '⑤防食機能の劣化(分類1)-e']}
    picture_number = models.CharField(max_length=255, null=True, blank=True) # '写真番号-31'
    this_time_picture = models.CharField(max_length=255, null=True, blank=True) # 'infra/img\\9月7日\u3000佐藤\u3000地上\\P9070617.JPG'
    last_time_picture = models.CharField(max_length=255, null=True, blank=True) # None
    textarea_content = models.CharField(max_length=255) # '排水管に板厚減少を伴う拡がりのある腐食,点錆が見られる。\n【関連損傷】\n排水管 Dp0101:⑤防食機能の劣化(分類1)-e'
    damage_coordinate_x = models.CharField(max_length=255) # '538482.3557216563', '229268.8593029478'
    damage_coordinate_y = models.CharField(max_length=255) # '538482.3557216563', '229268.8593029478'
    picture_coordinate_x = models.CharField(max_length=255, null=True, blank=True) # '538810.3087944178', '228910.3502713814'
    picture_coordinate_y = models.CharField(max_length=255, null=True, blank=True) # '538810.3087944178', '228910.3502713814'
    span_number = models.CharField(max_length=255) # 1径間
    special_links = models.CharField(max_length=255) # 排水管 Dp00/①腐食(大大)-e/1径間
    measurement = models.CharField(max_length=255, null=True, blank=True) # 面積
    damage_size = models.CharField(max_length=255, null=True, blank=True) # 100×100
    classification = models.CharField(max_length=255, null=True, blank=True) # 分類「1」
    pattern = models.CharField(max_length=255, null=True, blank=True) # パターン「6」
    excel_parts_name = models.CharField(max_length=255, null=True, blank=True) # エクセル出力（部材名称）
    excel_parts_number = models.CharField(max_length=255, null=True, blank=True) # エクセル出力（部材番号）
    excel_damage_name = models.CharField(max_length=255, null=True, blank=True) # エクセル出力（損傷名称）
    excel_damage_lank = models.CharField(max_length=255, null=True, blank=True) # エクセル出力（損傷判定）
    infra = models.ForeignKey(Infra, verbose_name="Infra", on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    class Meta:
        # ユニークの設定(fieldsの組み合わせを一意とする。nullが許可されているとデータが重複する可能性があるため、notnullの要素を扱う)
        constraints = [
            models.UniqueConstraint(fields=['parts_name', 'damage_name', 'parts_split', 'join', 'this_time_picture', 'infra', 'article',
                                            'damage_coordinate_x', 'damage_coordinate_y', 'span_number', 'special_links'], name='unique_parts_damage')
        ]
    def __str__(self):
        return f"{self.parts_name}　{self.damage_name}：{self.span_number}　({self.special_links})"

# class ExcelNo10Output(models.Model):
#     picture_number = models.CharField(max_length=255) # 1
#     parts_name = models.CharField(max_length=255) # 主桁
#     parts_number = models.CharField(max_length=255) # 0101
#     damage_name = models.CharField(max_length=255) # 腐食
#     damage_lank = models.CharField(max_length=255) # e
#     picture_url = models.ImageField(upload_to='photos/') # 写真データ
#     memo = models.TextField()# models.TextField()：文字数上限なし
#     article = models.ForeignKey(Article, on_delete=models.CASCADE) # 一意にするためのarticle
#     infra = models.ForeignKey(Infra, verbose_name="橋梁名", on_delete=models.CASCADE) # 一意にするためのinfra
#     class Meta:
#         # ユニークの設定(fieldsの組み合わせを一意とする。nullが許可されているとデータが重複する可能性があるため、notnullの要素を扱う)
#         constraints = [
#             models.UniqueConstraint(fields=['picture_number', 'infra', 'article'], name='unique_excel_number10')
#         ]
    
# << 損傷データを所見用に変換して登録 >>
class DamageList(models.Model):
    parts_name = models.CharField(max_length=255) # 主桁
    symbol = models.CharField(max_length=255) # Mg
    number = models.CharField(max_length=255) # 0101
    material = models.CharField(max_length=255) # S,C
    main_parts = models.CharField(max_length=255) # 主要部材「〇」
    damage_name = models.CharField(max_length=255) # 腐食
    damage_lank = models.CharField(max_length=255, null=True, blank=True)
    classification = models.CharField(max_length=255, null=True, blank=True) # 分類「1」
    pattern = models.CharField(max_length=255, null=True, blank=True) # パターン「6」
    span_number = models.CharField(max_length=255)
    infra = models.ForeignKey(Infra, verbose_name="Infra", on_delete=models.CASCADE) # サンプル橋
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parts_name', 'symbol', 'number', 'material', 'main_parts', 
                                            'damage_name', 'span_number', 'infra'], name='unique_damage_list')
        ]
    def __str__(self):
        return f"{self.parts_name} {self.symbol}{self.number}({self.damage_name}：{self.damage_lank})"
    
# << 所見コメントの登録 >>
class DamageComment(models.Model):
    parts_name = models.CharField(max_length=255) # 排水管 00
    comment_parts_name = models.CharField(max_length=255) # 排水管
    replace_name = models.CharField(max_length=255) # 50(排水管)
    parts_number = models.CharField(max_length=255, null=True, blank=True) # 00
    main_parts = models.CharField(max_length=255) # 主要部材「〇」
    material = models.CharField(max_length=255) # S,C
    damage_name = models.CharField(max_length=255) # 腐食
    number = models.IntegerField(null=True, blank=True) # 1(腐食)
    damage_max_lank = models.CharField(max_length=255, null=True, blank=True) # e
    damage_min_lank = models.CharField(max_length=255, null=True, blank=True) # b
    this_time_picture = models.CharField(max_length=255, null=True, blank=True) # 表示する写真
    jadgement = models.CharField(max_length=255, null=True, blank=True) # 対策区分「C1」
    cause = models.CharField(max_length=255, null=True, blank=True) # 損傷原因「経年変化」
    comment = models.CharField(max_length=255, null=True, blank=True) # 〇〇が見られる。
    auto_comment = models.CharField(max_length=255, null=True, blank=True) # 自動表示のコメント
    span_number = models.CharField(max_length=255) # 1(径間)
    infra = models.ForeignKey(Infra, verbose_name="Infra", on_delete=models.CASCADE) # サンプル橋
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    
    """ 並び替えに必要な動作(値を入れるフィールドを用意) """
    def save(self, *args, **kwargs):
        replace_dict = { # DamageCommentのreplace_nameに格納される番号
            "主桁": "101",
            "横桁": "102",
            "縦桁": "103",
            "床版": "104",
            "対傾構": "105",
            "上横構": "106",
            "下横構": "107",
            "アーチリブ": "108",
            "補剛桁": "109",
            "吊り材": "110",
            "支柱": "111",
            "橋門構": "112",
            "外ケーブル": "113",
            "ゲルバー部": "114",
            "PC定着部": "115",
            "格点": "116",
            "コンクリート埋込部": "117",
            "その他": "118",
            "橋脚[柱部・壁部]": "201",
            "橋脚[梁部]": "202",
            "橋脚[隅角部・接合部]": "203",
            "橋台[胸壁]": "204",
            "橋台[竪壁]": "205",
            "橋台[翼壁]": "206",
            "基礎[フーチング]": "207",
            "基礎": "208",
            "支承本体": "301",
            "アンカーボルト": "302",
            "沓座モルタル": "303",
            "台座コンクリート": "304",
            "落橋防止システム": "305",
            "高欄": "401",
            "防護柵": "402",
            "地覆": "403",
            "中央分離帯": "404",
            "伸縮装置": "405",
            "遮音施設": "406",
            "照明施設": "407",
            "縁石": "408",
            "舗装": "409",
            "排水ます": "410",
            "排水管": "411",
            "点検施設": "412",
            "添架物": "413",
            "袖擁壁": "414",
        }
        # 正規表現でスペース+2桁以上の数字を抽出
        match = re.search(r'(\D+)\s(\d{2,})', self.parts_name)
        
        if match:
            original_name = match.group(1).strip()
            self.comment_parts_name = original_name
            self.parts_number = match.group(2)
        else:
            original_name = self.parts_name
            self.comment_parts_name = original_name
            self.parts_number = '00'
        # 辞書を使って置換(部分一致)
        if original_name in replace_dict:
            # 置換処理
            for key in replace_dict.keys():
                if key in original_name:
                    # 対応する値に置き換える
                    self.replace_name = replace_dict[key]
                    break
        else:
            self.replace_name = original_name
            
        # materialの部分一致チェックとnumberの設定
        if '腐食' in self.damage_name:
            self.number = 1
        elif '亀裂' in self.damage_name:
            self.number = 2
        elif 'ゆるみ・脱落' in self.damage_name:
            self.number = 3
        elif '破断' in self.damage_name:
            self.number = 4
        elif '防食機能の劣化' in self.damage_name:
            self.number = 5
        elif 'ひびわれ' in self.damage_name:
            self.number = 6
        elif '剥離・鉄筋露出' in self.damage_name:
            self.number = 7
        elif '漏水・遊離石灰' in self.damage_name:
            self.number = 8
        elif '抜け落ち' in self.damage_name:
            self.number = 9
        elif '補修・補強材の損傷' in self.damage_name:
            self.number = 10
        elif '床版ひびわれ' in self.damage_name:
            self.number = 11
        elif 'うき' in self.damage_name:
            self.number = 12
        elif '遊間の異常' in self.damage_name:
            self.number = 13
        elif '路面の凹凸' in self.damage_name:
            self.number = 14
        elif '舗装の異常' in self.damage_name:
            self.number = 15
        elif '支承部の機能障害' in self.damage_name:
            self.number = 16
        elif '定着部の異常' in self.damage_name:
            self.number = 18
        elif '変色・劣化' in self.damage_name:
            self.number = 19
        elif '漏水・滞水' in self.damage_name:
            self.number = 20
        elif '異常な音・振動' in self.damage_name:
            self.number = 21
        elif '異常なたわみ' in self.damage_name:
            self.number = 22
        elif '変形・欠損' in self.damage_name:
            self.number = 23
        elif '土砂詰まり' in self.damage_name:
            self.number = 24
        elif '沈下・移動・傾斜' in self.damage_name:
            self.number = 25
        elif '洗掘' in self.damage_name:
            self.number = 26
        elif 'NON' in self.damage_name:
            self.number = 27
        else:
            self.number = 17
        # get_combined_textメソッドで生成されたテキストをauto_commentフィールドに代入
        if self.damage_name == "NON":
            self.auto_comment = "健全である。"
        else:
            self.auto_comment = self.get_combined_text()

        super().save(*args, **kwargs)
    """"""
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parts_name', 'main_parts', 'damage_name', 'span_number', 'infra'], name='unique_damage_comment')
        ]
    def __str__(self):
        return f"{self.parts_name}　{self.damage_name}：{self.jadgement}　({self.cause})"
    
    def get_combined_text(self):
        if self.damage_name == "腐食": # 1：腐食
            if self.damage_max_lank == "b":
                name_lank = "軽微な腐食"
            elif self.damage_max_lank == "c":
                name_lank = "全体的かつ軽微な腐食"
            elif self.damage_max_lank == "d":
                name_lank = "板厚減少を伴う腐食"
            else:
                name_lank = "全体的かつ板厚減少を伴う腐食"           
        elif self.damage_name == "剥離・鉄筋露出": # 7：剥離・鉄筋露出
            if self.damage_max_lank == "c":
                name_lank = "剥離"
            elif self.damage_max_lank == "d":
                name_lank = "鉄筋露出"
            else:
                name_lank = "鉄筋の減肉を伴う鉄筋露出"
        elif self.damage_name == "抜け落ち": # 9：抜け落ち
            name_lank = "コンクリート塊の抜け落ち"
        elif self.damage_name == "うき": # 12：うき
            name_lank = "コンクリートのうき"
        elif self.damage_name == "漏水・滞水": # 20：漏水・滞水
            name_lank = "本来の排水機能によらない漏水・構造物に支障を及ぼす可能性のある滞水"
        elif self.damage_name == "変形・欠損": # 23：変形・欠損
            if self.damage_max_lank == "c":
                name_lank = "局部的な変形・欠損"
            else:
                name_lank = "著しい変形・欠損"
        elif self.damage_name == "土砂詰まり": # 24：土砂詰まり
            name_lank = "土砂の堆積"
        elif self.damage_name.startswith("その他"): # 17：その他
            # 正規表現で「:」と「)」の間の文字を抽出
            match = re.search(r':(.*?)\)', self.damage_name)
            if match:
                name_lank = match.group(1)
            else:
                name_lank = ""
        else:
            name_lank = "損傷"
        # 判定区分に対する定型文
        if self.jadgement == "B":
            jadgement_text = "状況に応じて補修を行う必要がある。"
        elif self.jadgement == "M":
            jadgement_text = "維持工事で対応する必要がある。"
        elif self.jadgement == "C1":
            jadgement_text = "予防保全の観点から、速やかに補修等を行う必要がある。"
        elif self.jadgement == "C2":
            jadgement_text = "橋梁構造の安全性の観点から、速やかに補修等を行う必要がある。"
        elif self.jadgement == "S1":
            jadgement_text = "詳細調査の必要がある。"
        elif self.jadgement == "S2":
            jadgement_text = "追跡調査の必要がある。"
        elif self.jadgement == "E1":
            jadgement_text = "橋梁構造の安全性の観点から、緊急対応の必要がある。"
        elif self.jadgement == "E2":
            jadgement_text = "その他、緊急対応の必要がある。"
        else:
            jadgement_text = ""
            
        pattern = r'\d{2,}'
        # 2桁以上の数字を空文字に置換して削除
        self.comment_parts_name = re.sub(pattern, '', self.comment_parts_name)
            
        return f"{self.comment_parts_name}に{name_lank}が見られる。{jadgement_text}"