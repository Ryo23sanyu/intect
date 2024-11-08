from collections import defaultdict
import fnmatch
from functools import reduce
from itertools import groupby
from operator import attrgetter
import os
from pathlib import Path
import re
from urllib.parse import unquote
import boto3
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from django.views import View
import ezdxf
import urllib

from infra.tasks import create_picturelist

from .forms import DamageCommentCauseEditForm, DamageCommentEditForm, DamageCommentJadgementEditForm, NameEntryForm, PartsNumberForm, TableForm
from .models import Approach, Article, BridgePicture, DamageComment, DamageList, FullReportData, Infra, LoadGrade, LoadWeight, NameEntry, PartsName, PartsNumber, Regulation, Rulebook, Table, Thirdparty, UnderCondition

# << indexページ(使用方法) >>
def index_view(request):
    return render(request, 'infra/how_to_use.html')

# << 案件・一覧 >>
class ListArticleView(LoginRequiredMixin, ListView):
    template_name = 'infra/article_list.html'
    model = Article
    
# << 案件・詳細 >>
class DetailArticleView(LoginRequiredMixin, DetailView):
    template_name = 'infra/article_detail.html'
    model = Article
    
# << 案件・作成 >>
class CreateArticleView(LoginRequiredMixin, CreateView):
    template_name = 'infra/article_create.html'
    model = Article
    fields = ('案件名', '土木事務所', '対象数', '担当者名', 'その他')
    success_url = reverse_lazy('list-article')
    
# << 案件・削除 >>
class DeleteArticleView(LoginRequiredMixin, DeleteView):
    template_name = 'infra/article_delete.html'
    model = Article
    success_url = reverse_lazy('list-article')
    
# << 案件・更新 >>
class UpdateArticleView(LoginRequiredMixin, UpdateView):
    template_name = 'infra/article_update.html'
    model = Article
    fields = ('案件名', '土木事務所', '対象数', '担当者名', 'その他')
    success_url = reverse_lazy('list-article')


# << 橋梁・一覧 >>
class ListInfraView(LoginRequiredMixin, ListView):
    template_name = 'infra/infra_list.html'
    model = Infra # 使用するモデル「infra」
    def get_queryset(self, **kwargs):
        # モデル検索のクエリー。Infra.objects.all() と同じ結果で全ての Infra
        queryset = super().get_queryset(**kwargs)
        queryset = queryset.filter(article = self.kwargs["article_pk"])
        return queryset
    def get_context_data(self, **kwargs):
        kwargs["article_id"] = self.kwargs["article_pk"]
        return super().get_context_data(**kwargs)
      
      
# << 橋梁・詳細 >>
class DetailInfraView(LoginRequiredMixin, DetailView):
    template_name = 'infra/infra_detail.html'
    model = Infra
    def get_context_data(self, **kwargs):
        # HTMLテンプレートでの表示変数として「article_id」を追加。
        # 値はパスパラメータpkの値→取り扱うarticle.idとなる
        kwargs["article_id"] = self.kwargs["article_pk"]
        #モデルのTableクラス ↑                    ↑  infraに格納する値は自らのpkの値とする
        return super().get_context_data(**kwargs)
      
# << 橋梁・作成 >>
class CreateInfraView(LoginRequiredMixin, CreateView):
    template_name = 'infra/infra_create.html'
    model = Infra
    fields = ('title', '径間数', '橋長', '全幅員','橋梁コード', '活荷重', '等級', '適用示方書', '路線名',
              '上部構造形式', '下部構造形式', '基礎構造形式', '近接方法', '交通規制', '第三者点検', '海岸線との距離', 
              '路下条件', '交通量', '大型車混入率', '特記事項', 'カテゴリー', 'latitude', 'longitude', 'end_latitude', 'end_longitude')
    success_url = reverse_lazy('detail-infra')
    
    def form_valid(self, form): # form_validはフォームが有効のとき呼び出される
        article_pk = self.kwargs['article_pk'] # URLパラメータからarticle_pkを取得
        print(article_pk)
        article = get_object_or_404(Article, pk=article_pk) # article_pkを使って、Articleモデルから対応するオブジェクトを取得。オブジェクトが見つからない場合は404エラーを返す
        print(article)
        form.instance.article = article # フォームインスタンス (form.instance) の articleフィールドに取得したarticleをセット
        print(form.instance)
        self.article = article # インスタンス変数として保存
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('list-infra', kwargs={'article_pk': self.article.pk})
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["loadWeights"] = LoadWeight.objects.all()
        context["loadGrades"] = LoadGrade.objects.all()
        context["rulebooks"] = Rulebook.objects.all()
        context["approachs"] = Approach.objects.all()
        context["regulations"] = Regulation.objects.all()
        context["thirdpartys"] = Thirdparty.objects.all()
        context["underconditions"] = UnderCondition.objects.all()
        return context
      
# << 橋梁・削除 >>
class DeleteInfraView(LoginRequiredMixin, DeleteView):
    template_name = 'infra/infra_delete.html'
    model = Infra
    success_url = reverse_lazy('list-infra')
    def get_success_url(self):
        return reverse_lazy('list-infra', kwargs={'article_pk': self.kwargs["article_pk"]})
      
# << 橋梁・更新 >>
class UpdateInfraView(LoginRequiredMixin, UpdateView):
    template_name = 'infra/infra_update.html'
    model = Infra
    fields = ('title', '径間数', '橋長', '全幅員', 'latitude', 'longitude', '橋梁コード', '活荷重', '等級', '適用示方書', 
              '上部構造形式', '下部構造形式', '基礎構造形式', '近接方法', '交通規制', '第三者点検', '海岸線との距離', 
              '路下条件', '交通量', '大型車混入率', '特記事項', 'カテゴリー', 'article')
    success_url = reverse_lazy('detail-infra')
    def get_success_url(self):
        return reverse_lazy('detail-infra', kwargs={'article_pk': self.kwargs["article_pk"], 'pk': self.kwargs["pk"]})

    #新規作成時、交通規制の全データをコンテキストに含める。
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_regulations = self.object.交通規制.values_list('id', flat=True)# 選択状態を保持
        context['selected_regulations'] = list(selected_regulations)# 選択状態を保持
        context["regulations"] = Regulation.objects.all()
        
        selected_loadWeights = self.object.活荷重.values_list('id', flat=True)
        context['selected_loadWeights'] = list(selected_loadWeights)
        context["loadWeights"] = LoadWeight.objects.all()
        
        selected_loadGrades = self.object.等級.values_list('id', flat=True)
        context['selected_loadGrades'] = list(selected_loadGrades)
        context["loadGrades"] = LoadGrade.objects.all()
        
        selected_rulebooks = self.object.適用示方書.values_list('id', flat=True)
        context['selected_rulebooks'] = list(selected_rulebooks)
        context["rulebooks"] = Rulebook.objects.all()
        
        selected_approachs = self.object.近接方法.values_list('id', flat=True)
        context['selected_approachs'] = list(selected_approachs)
        context["approachs"] = Approach.objects.all()
        
        selected_thirdpartys = self.object.第三者点検.values_list('id', flat=True)
        context['selected_thirdpartys'] = list(selected_thirdpartys)
        context["thirdpartys"] = Thirdparty.objects.all()
        
        selected_underconditions = self.object.路下条件.values_list('id', flat=True)
        context['selected_underconditions'] = list(selected_underconditions)
        context["underconditions"] = UnderCondition.objects.all()
        return context

# << ファイルアップロード >>
class UploadView(View):

    def get(self, request, *args, **kwargs):

        context = {}
        context["form"] = TableForm()

        return render(request, "infra/index.html", context)

    def post(self, request, *args, **kwargs):

        form = TableForm(request.POST, request.FILES)

        if form.is_valid():
            print("保存")
            form.save()
        else:
            print(form.errors)

        return redirect("upload")

index   = UploadView.as_view()

# << 名前とアルファベットの登録 >>
def names_list(request, article_pk):
    
    alphabet_list = request.POST.getlist("name_alphabet")
    
    alphabet_list_count = len(alphabet_list)
    for i in range(0, alphabet_list_count, 2):
        dic = {}
        dic["name"] = alphabet_list[i]
        dic["alphabet"] = alphabet_list[i+1]
        dic["article"] = article_pk
        
        form = NameEntryForm(dic)

        if form.is_valid():
            form.save()
        else:
            print(form.errors) # 入力フォームのエラー内容を表示
            
    name_entries = NameEntry.objects.filter(article=article_pk)
    
    return render(request, 'infra/names_list.html', {'article_pk': article_pk, "form": NameEntryForm(), 'name_entries': name_entries})

# << 登録した名前を削除 >>
def delete_name_entry(request, entry_id):
    entry = get_object_or_404(NameEntry, pk=entry_id)
    article_pk = entry.article.pk  # 事前に記事のPKを取得
    if request.method == 'POST':    
        entry.delete()
    name_entries = NameEntry.objects.filter(article=article_pk)
    return render(request, 'infra/names_list.html', {'article_pk': article_pk, "form": NameEntryForm(), 'name_entries': name_entries})

# << 要素番号の登録 >>
def number_list(request, article_pk, pk):
    
    parts_names = PartsName.objects.all().order_by('display_order')  # 順序フィールドで部材名を取り出し並べ替え
    # 同じname属性の値をすべて取り出す
    serial_numbers = request.POST.getlist("serial_number") # ['0101', '0103', '0201', '0203']
    single_numbers = request.POST.getlist("single_number") # ['0101', '0201', '0301', '0401']
    
    new_serial_numbers = []
    serial_numbers_count = len(serial_numbers)
    #    初期値を0 ↓     回数分 ↓           ↓ 2ずつ足す(0101(index:0),0201(index:2))
    for i in range(0, serial_numbers_count, 2):
        new_serial_numbers.append(serial_numbers[i] + "~" + serial_numbers[i+1])
        #                          0101(index:0) ↑          0103(index:1+1) ↑
        #                          0201(index:2) ↑          0203(index:2+1) ↑
    print(new_serial_numbers) # ['0101~0103', '0201~0203']
    
    # 単一の番号、連続の番号 を部材名と紐付けて保存
    for new_serial_number in new_serial_numbers:
        print(new_serial_number)
        if "~" in new_serial_number and len(new_serial_number) >= 5: # 01～02(5文字)
            # new_serial_number = "0101~0205"
            one = new_serial_number.find("~")

            start_number = new_serial_number[:one]
            end_number = new_serial_number[one+1:]

            # 最初の2桁と最後の2桁を取得
            start_prefix = start_number[:2]
            start_suffix = start_number[2:]
            end_prefix = end_number[:2]
            end_suffix = end_number[2:]

            first_elements = []
            # 決められた範囲内の番号を一つずつ追加
            for prefix in range(int(start_prefix), int(end_prefix)+1):
                for suffix in range(int(start_suffix), int(end_suffix)+1):
                    number_items = "{:02d}{:02d}".format(prefix, suffix)
                    dic = {} # forms.pyにも入れないと自動登録ができない
                    dic["number"] = number_items
                    dic["parts_name"] = request.POST.get("parts_name")
                    dic["symbol"] = request.POST.get("symbol")
                    dic["material"] = request.POST.getlist("material")
                    dic["span_number"] = request.POST.get("span_number")
                    dic["main_frame"] = request.POST.get("main_frame") == 'on'
                    dic["infra"] = pk # infraとの紐付け
                    dic["article"] = article_pk
                    print(f"new_serial_number:{number_items}")
                    
                    # 1個ずつバリデーションして保存する
                    form = PartsNumberForm(dic)

                    if form.is_valid():
                        form.save()
                        parts_number = form.save()
                        parts_number.material.set(request.POST.getlist("material"))
                    else:
                        print(form.errors) # 入力フォームのエラー内容を表示
                        
    for single_number in single_numbers:
        if single_number.isdigit():
            dic = {}
            dic["number"] = single_number
            dic["parts_name"] = request.POST.get("parts_name")
            dic["symbol"] = request.POST.get("symbol")
            dic["material"] = request.POST.getlist("material")
            dic["span_number"] = request.POST.get("span_number")
            dic["main_frame"] = request.POST.get("main_frame") == 'on'
            dic["infra"] = pk # infraとの紐付け
            dic["article"] = article_pk 
            print(single_number)

            # 1個ずつバリデーションして保存する
            form    = PartsNumberForm(dic)

            if form.is_valid():
                form.save()
                parts_number = form.save()
                parts_number.material.set(request.POST.getlist("material"))
            else:
                print(form.errors)

    print(f"pk：{pk}、article_pk：{article_pk}")
    create_number_list = PartsNumber.objects.filter(infra=pk)
    print(f"create_number_list：{create_number_list}")
    print("-----------------------------------------")
    print(f"橋梁番号:{pk}") # 橋梁番号:Table object (1)
    print(f"案件番号:{article_pk}") # 案件番号:1
    number_object = Infra.objects.filter(id=pk).first()
    print(f"サイドバーに渡すID：{number_object}")
    for item in create_number_list:
        print(f"Number: {item.number}, Unique ID: {item.unique_id}")

    grouped_parts = defaultdict(list)
    for accordion_list in create_number_list:
        title = f"{accordion_list.parts_name.部材名}（{accordion_list.symbol}）{accordion_list.get_material_list()} {accordion_list.span_number}径間"
        grouped_parts[title].append({
        'number': accordion_list.number,
        'unique_id': accordion_list.unique_id
        })

    return render(request, 'infra/number_entry.html', {'object': number_object, 'article_pk': article_pk, 'pk': pk, "form": PartsNumberForm(), 'create_number_list': create_number_list, 'grouped_parts': grouped_parts.items(), 'parts_names': parts_names})

# << 登録した番号を削除 >>
def delete_number(request, article_pk, pk, unique_id):
    print(f"{article_pk}/{pk}")
    if request.method == 'POST':
        print(f"削除対象：{PartsNumber.objects.filter(infra=pk, article=article_pk)}")
        parts_number = get_object_or_404(PartsNumber, infra=pk, article=article_pk, unique_id=unique_id)
        parts_number.delete()
        return redirect('number-list', article_pk=article_pk, pk=pk)

# << 部材名と記号を紐付けるAjaxリクエスト >>
def get_symbol(request):
    part_id = request.GET.get('part_id')
    try:
        parts_name = PartsName.objects.get(id=part_id)
        return JsonResponse({'symbol': parts_name.記号})
    except PartsName.DoesNotExist:
        return JsonResponse({'error': 'PartsName not found'}, status=404)
    
# 番号表示 TODO:無くても良い
def number_view(request):
    # PartsNumberモデルから1件データを取り出し
    parts_number = PartsNumber.objects.get(id=1)
    # 抽出した数字を文字列として結合
    result = ""
    # 4桁 か 4桁~4桁 のいずれか
    if len(parts_number.number) == 4:
        # 4桁
        result  = parts_number.number
    else:
        # 4桁~4桁
        # ~ で区切る必要がある。 [ "3000","3000" ]
        numbers = parts_number.number.split("~")
        start   = numbers[0]
        end     = numbers[1]
        # 最初の2桁と最後の2桁を取得
        start_prefix = start[:2]
        start_suffix = start[2:]
        end_prefix = end[:2]
        end_suffix = end[2:]

        for prefix in range(int(start_prefix), int(end_prefix)+1):
            for suffix in range(int(start_suffix), int(end_suffix)+1):
                result += "{:02d}{:02d}\n".format(prefix, suffix)

    print(result)

def match_s3_objects_with_prefix(bucket_name, prefix, pattern):
    s3 = boto3.client('s3')
    # プレフィックス(特定のフォルダ)を指定して、オブジェクトをリスト
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if 'Contents' not in response:
        return []
    # パターンに基づいてオブジェクトをフィルタリング
    matched_keys = [obj['Key'] for obj in response['Contents'] if fnmatch.fnmatch(obj['Key'], pattern)]
    return matched_keys


# << 損傷写真帳の作成 >>
def bridge_table(request, article_pk, pk): # idの紐付け infra/bridge_table.htmlに表示
    context = {}
    # プロジェクトのメディアディレクトリからdxfファイルまでの相対パス
    # URL：article/<int:article_pk>/infra/<int:pk>/bridge-table/

    # 指定したInfraに紐づく Tableを取り出す
    article = Article.objects.filter(id=article_pk).first()
    infra = Infra.objects.filter(id=pk).first()
    table = Table.objects.filter(infra=pk).first()
    # << 案件名とファイル名を連結してdxfファイルのURLを取得する >>
    # AWSクライアントを作成
    s3 = boto3.client('s3')
    
    bucket_name = 'infraprotect'
    print(bucket_name)
    folder_name = article.案件名+"/"
    print(folder_name)
    pattern = f'*{infra.title}*/{infra.title}.dxf'
    print(pattern)

    # 該当するオブジェクトを取得
    matched_objects = match_s3_objects_with_prefix(bucket_name, folder_name, pattern)

    if matched_objects:
        print(f"該当オブジェクト：{matched_objects}")
    else:
        print("ファイルが見つかりません")

    # 結果を表示
    for obj_key in matched_objects:
        encode_dxf_filename = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{obj_key}"
    
    dxf_filename = urllib.parse.quote(encode_dxf_filename, safe='/:') # スラッシュとコロン以外をエンコード

    print(f"dxfファイルのデコードURLは：{encode_dxf_filename}")
    print(f"dxfファイルの絶対URLは：{dxf_filename}")
    
    # bridge_tableのボタンを押したときのアクション
    second_search_title_text = "損傷図"
    # << 辞書型として、全径間を1つの多重リストに格納 >>
    max_search_title_text = infra.径間数
    print(f"最大径間数：{max_search_title_text}")
    database_sorted_items = []  # 結果をまとめるリスト
    
    for search_title_text_with_suffix in range(1, max_search_title_text + 1):
        search_title_text = f"{search_title_text_with_suffix}径間"
        
        print(search_title_text)
        #                                                                                   1径間                  損傷図
        sub_database_sorted_items = create_picturelist(request, table, dxf_filename, search_title_text, second_search_title_text)

        for item in sub_database_sorted_items:
            item['search'] = search_title_text
            database_sorted_items.append(item)

    """辞書型の多重リストをデータベースに登録"""
    # << ['']を外してフラットにする >>
    def flatten(value):
        def _flatten(nested_list):
            if isinstance(nested_list, list):
                for item in nested_list:
                    yield from _flatten(item)
            else:
                yield nested_list
        
        return ', '.join(_flatten(value))

    # << joinキーを変換 >>
    def join_to_result_string(join):
        result_parts = []
        for item in join:
            parts_name = item['parts_name'][0]
            damage_names = item['damage_name']
            formatted_damage_names = '/'.join(damage_names)
            result_parts.append(f"{parts_name} : {formatted_damage_names}")
        return ', '.join(result_parts)

    # << 写真のキーを変換 >>
    def simple_flatten(value):
        return ', '.join(map(str, value)) if isinstance(value, list) else value
    
    # <<正規表現で4桁以上の番号を取得>>
    def extract_number(text):
        pattern = r'\d{4,}' # 4文字以上の連続する数字
        matches = re.findall(pattern, text)
        return matches
    
    picture_counter = 1
    index_counter = 0
    picture_number_box = []

    for damage_data in database_sorted_items:
        # 元の辞書から 'picture_number' の値を取得
        #             　辞書型 ↓           ↓ キーの名前      ↓ 存在しない場合、デフォルト値として空白を返す
        picture_number = damage_data.get('picture_number', '')
        # 正規表現で数字のみを抽出
        if picture_number:
            # 数字のみを抽出
            before_numbers_only = re.findall(r'\d+', str(picture_number)) # ['2']  ['2','3']
            #print(f"リスト型番号:{before_numbers_only}")
            #print(f"{index_counter}  どっちが大きい　{len(before_numbers_only)}")
            # before_numbers_onlyの各元素で別の処理を行う場合
            # カウンターに基づいて処理を行う
            if index_counter == 0:
                picture_number_box = []
            if len(before_numbers_only) > 1:
                for number in before_numbers_only:
                    #print(f"{index_counter}番目の要素: {number}")
                    picture_number_box.append(number)
                    index_counter += 1
                index_counter = 0
                #print(picture_number_box)
            else:
                picture_number_box = []
                index_counter = 0
                numbers_only = before_numbers_only[index_counter]  # カウンターに対応する数字を取得
                #print(f"オンリーナンバーズ（抽出後）: {numbers_only}")
                picture_number_box.append(numbers_only)
        else:
            numbers_only = None

        damage_coordinate = damage_data.get('damage_coordinate', [None, None])
        damage_coordinate_x = damage_coordinate[0] if damage_coordinate else None
        damage_coordinate_y = damage_coordinate[1] if damage_coordinate else None

        picture_coordinate = damage_data.get('picture_coordinate', [None, None])
        picture_coordinate_x = picture_coordinate[0] if picture_coordinate else None
        picture_coordinate_y = picture_coordinate[1] if picture_coordinate else None

        #parts_list = flatten(damage_data.get('parts_name', ''))
        #damage_list = flatten(damage_data.get('damage_name', ''))

        names = damage_data.get('parts_name', '')
        damages = damage_data.get('damage_name', '')
        #print(f"names:{names}")
        print(f"damages:{damages}")
        
        split_names = []

        for item in names:
            split_items = []
            for split in item:
                if "～" in split:
                    one = split.find("～")
                    start_number = ''.join(extract_number(split[:one])) # 0101
                    end_number = ''.join(extract_number(split[one+1:])) # 0204

                    # 最初の2桁と最後の2桁を取得
                    start_prefix = start_number[:2] # 01
                    start_suffix = start_number[2:] # 01
                    end_prefix = end_number[:2] # 01
                    end_suffix = end_number[2:] # 03
                    
                    part_name = split[:one].replace(start_number, '')
                
                    for prefix in range(int(start_prefix), int(end_prefix)+1):
                        for suffix in range(int(start_suffix), int(end_suffix)+1):
                            number_items = "{:02d}{:02d}".format(prefix, suffix)
                            split_items.append(part_name + number_items)
                else:
                    split_items.append(split)
            split_names.append(split_items)
        
        join = join_to_result_string(damage_data.get('join', ''))
        this_time_picture = simple_flatten(damage_data.get('this_time_picture', ''))
        last_time_picture = simple_flatten(damage_data.get('last_time_picture', ''))
        textarea_content = damage_data.get('textarea_content', '')
        span_number = damage_data.get('search', '')
        #print("----------------------------------")
        #print(f"damage_data:{damage_data}")
        #print(f"join:{join}")
        #print(f"this_time_picture:{this_time_picture}")
        name_length = len(split_names)
        damage_length = len(damages)
        
        # 多重リストかどうかを判定する関数
        def is_multi_list(lst):
            return any(isinstance(i, list) for i in lst)
        
        def process_names(names):
            """
            与えられたnamesを処理し、適切な部分を返す関数
            所見用にparts_splitに格納
            """
            parts_left = ["主桁", "PC定着部"]# 左の数字
            parts_right = ["横桁", "橋台[胸壁]", "橋台[竪壁]"]# 右の数字
            parts_zero = ["床版"]# 00になる場合

            # namesから部品名（parts）と数字を抽出
            space = names.find(" ")
            parts = names[:space]  # 部品名
            number = ''.join(extract_number(names))  # 数字
            parts_join = names.replace(number, '') # 符号部分を取得

            # 必要な部分の数字を抽出するロジック
            split_number = ''

            if parts in parts_zero:
                split_number = '00'
            elif len(number) == 4 or int(number[2:]) >= 100:
                if parts in parts_left:
                    split_number = number[:2]
                elif parts in parts_right:
                    split_number = number[2:]
                else:
                    split_number = '00'
            else:
                if parts in parts_left:
                    split_number = number[:3]
                elif parts in parts_right:
                    split_number = number[3:]
                else:
                    split_number = '00'

            result = parts_join + split_number  # 結果を組み立てる
            return result
            # 共通のフィールドを辞書に格納
        infra = Infra.objects.filter(id=pk).first()
        article = infra.article
        table = Table.objects.filter(infra=infra.id, article=article.id).first()
        #print(table) # 旗揚げチェック：お試し（infra/table/dxf/121_2径間番号違い.dxf）
        
        # << 管理サイトに登録するコード（損傷写真帳） >>
        if not is_multi_list(split_names) and not is_multi_list(damages) and name_length == 1: # 部材名が1つの場合
            picture_number_index = 0 # 写真番号は0から始める
            for single_damage in damages: 
                parts_name = names[0]
                pattern = r"(\d+)$"
                # parts_nameからパターンにマッチする部分を検索
                match = re.search(pattern, parts_name)
                if match:
                    four_numbers = match.group(1)
                else:
                    four_numbers = "00"
                damage_name = flatten(single_damage)
                # print(f"parts_name1:{parts_name}") # 主桁 Mg0101
                # print(f"damage_name1:{damage_name}") # ㉓変形・欠損-c
                parts_split = process_names(flatten(parts_name))
                # print(f"this_time:{this_time_picture}")
                list_in_picture = this_time_picture.split(",")
                for single_picture in list_in_picture:
                    update_fields = {
                        'parts_name': parts_name,
                        'four_numbers': four_numbers,
                        'damage_name': damage_name,
                        'parts_split': parts_split,
                        'join': join,
                        'this_time_picture': single_picture,
                        'last_time_picture': last_time_picture,
                        'textarea_content': textarea_content,
                        'damage_coordinate_x': damage_coordinate_x,
                        'damage_coordinate_y': damage_coordinate_y,
                        'picture_coordinate_x': picture_coordinate_x,
                        'picture_coordinate_y': picture_coordinate_y,
                        'span_number': span_number,
                        'special_links': '/'.join([str(parts_split), str(damage_name), str(span_number)]),
                        'infra': infra,
                        'article': article,
                        'table': table
                    }
                    # print(f"update_fields：{update_fields}")
                #print(f"径間番号:{span_number}")
                # if FullReportData.objects.filter(join=join, this_time_picture=this_time_picture, span_number=span_number, table=table, damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y):
                    # update_fields['this_time_picture'] = ""

                    if single_picture:
                        images = [single_picture]
                        update_fields['picture_number'] = picture_counter
                        picture_counter += 1
                        # BridgePictureモデルに保存
                        if numbers_only is not None and numbers_only != '':
                            # print(f"images：{images}") # ['写真パス1', '写真パス2']
                            for absolute_image_path in images:
                                # print(f"absolute_image_path：{absolute_image_path}") # 写真パス1（別データとして、写真パス2）
                                try:
                                # with open(absolute_image_path, 'rb') as image_file:
                                    #print(f"保存前：{numbers_only}")
                                    #print(f"オンリーナンバーズ（抽出後）: {picture_number_box}")
                                    if picture_number_index < len(picture_number_box):
                                        current_picture_number = picture_number_box[picture_number_index]
                                    else:
                                        current_picture_number = None
                                    # print(f"保存後：{current_picture_number}")
                                    #print("---------")
                                    if current_picture_number is None: # 写真がない
                                        join_picture_damage_name = BridgePicture.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                        # print(f"join_picture_damage_name：{join_picture_damage_name}")
                                        if join_picture_damage_name.first():
                                            for picture in join_picture_damage_name:
                                                #print(picture)
                                                if picture.damage_name:
                                                    # print(f"損傷名：{picture.damage_name}") # 損傷名
                                                    edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                                    new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                                    # 末尾のハイフン+任意の1文字を削除
                                                    damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                                    picture.memo = f"{picture.memo} / {parts_split},{damage_name}"
                                                else:
                                                    picture.memo = f"{parts_split},{damage_name}"
                                                picture.save()
                                            #print(join_picture_damage_name)
                                        #print("picture_number_boxのインデックスが範囲外です")
                                        continue
                                    # 「スペース + 2文字以上のアルファベット + 2文字以上の数字」にマッチする部分を捉える
                                    pattern = r'\s+[A-Za-z]{2,}[0-9]{2,}'
                                    # マッチした部分からアルファベット部分だけを削除するための関数を定義
                                    def remove_alphabets(match):
                                        # マッチした文字列からアルファベット部分を削除
                                        return re.sub(r'[A-Za-z]+', '', match.group())
                                            
                                    joined_picture_damage_name = FullReportData.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                    # print(f"joined_picture_damage_name：{joined_picture_damage_name}")
                                    
                                    loop_change = True
                                    for full_damaged_name in joined_picture_damage_name:
                                        if loop_change:
                                            print(full_damaged_name.join)
                                            loop_change = False
                                            
                                    # re.subでパターンにマッチする部分を編集
                                    edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                    new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                    damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                    # 写真の重複チェック(写真番号が同じ、損傷座標・def座標が同じ、径間番号・dxfファイル名・案件名・橋梁名が同じ)
                                    existing_picture = BridgePicture.objects.filter(
                                        picture_number=current_picture_number,
                                        damage_coordinate_x=damage_coordinate_x,
                                        damage_coordinate_y=damage_coordinate_y,
                                        picture_coordinate_x=picture_coordinate_x,
                                        picture_coordinate_y=picture_coordinate_y,
                                        span_number=span_number,
                                        table=table,
                                        article=article,
                                        infra=infra
                                    ).first()
                                    
                                    if existing_picture is None:
                                        bridge_picture = BridgePicture(
                                            image=absolute_image_path, 
                                            picture_number=current_picture_number,
                                            damage_name=damage_name,
                                            parts_split=edited_result_parts_name,
                                            memo=full_damaged_name.join,
                                            damage_coordinate_x=damage_coordinate_x,
                                            damage_coordinate_y=damage_coordinate_y,
                                            picture_coordinate_x=picture_coordinate_x,
                                            picture_coordinate_y=picture_coordinate_y,
                                            span_number=span_number,
                                            table=table,
                                            article=article,
                                            infra=infra
                                        )
                                        bridge_picture.save()
                                        picture_number_index += 1
                                except FileNotFoundError:
                                    print(f"ファイルが見つかりません: {absolute_image_path}")
           
                    else:
                        update_fields['picture_number'] = ""
                    
                report_data_exists = FullReportData.objects.filter(**update_fields).exists()
                if report_data_exists:
                    print("データが存在しています。")
                else:
                    try:
                        damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                        damage_obj.save()
                    except IntegrityError:
                        print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")
                    
                    
        elif not is_multi_list(split_names) and not is_multi_list(damages) and name_length >= 2: # 部材名が2つ以上の場合
            picture_number_index = 0
            if damage_length == 1: # かつ損傷名が1つの場合
                for parts_name in split_names:
                    pattern = r"(\d+)$"
                    # parts_nameからパターンにマッチする部分を検索
                    match = re.search(pattern, parts_name)
                    if match:
                        four_numbers = match.group(1)
                    else:
                        four_numbers = "00"
                    damage_name = flatten(damages[0])
                    # print(f"parts_name2:{parts_name}")
                    # print(f"damage_name2:{damage_name}")
                    parts_split = process_names(flatten(parts_name))
                    # print(f"this_time:{this_time_picture}")
                    list_in_picture = this_time_picture.split(",")
                    for single_picture in list_in_picture:
                        update_fields = {
                            'parts_name': parts_name,
                            'four_numbers': four_numbers,
                            'damage_name': damage_name,
                            'parts_split': parts_split,
                            'join': join,
                            'this_time_picture': single_picture,
                            'last_time_picture': last_time_picture,
                            'textarea_content': textarea_content,
                            'damage_coordinate_x': damage_coordinate_x,
                            'damage_coordinate_y': damage_coordinate_y,
                            'picture_coordinate_x': picture_coordinate_x,
                            'picture_coordinate_y': picture_coordinate_y,
                            'span_number': span_number,
                            'special_links': '/'.join([str(parts_split), str(damage_name), str(span_number)]),
                            'infra': infra,
                            'article': article,
                            'table': table
                        }         
                    #print(f"径間番号:{span_number}")                 
                    # if FullReportData.objects.filter(join=join, this_time_picture=this_time_picture, span_number=span_number, table=table, damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y):
                        # update_fields['this_time_picture'] = ""
                        # update_fields['picture_number'] = ""
                        
                        if single_picture:
                            images = [single_picture]
                            update_fields['picture_number'] = picture_counter
                            picture_counter += 1
                            # BridgePictureモデルに保存
                            if numbers_only is not None and numbers_only != '':
                                # print(f"images：{images}")
                                for absolute_image_path in images:
                                    # print(f"absolute_image_path：{absolute_image_path}")
                                    try:
                                    # with open(absolute_image_path, 'rb') as image_file:
                                        #print(f"保存前：{numbers_only}")
                                        #print(f"オンリーナンバーズ（抽出後）: {picture_number_box}")
                                        if picture_number_index < len(picture_number_box):
                                            current_picture_number = picture_number_box[picture_number_index]
                                        else:
                                            current_picture_number = None
                                        # print(f"保存後：{current_picture_number}")
                                        #print("---------")
                                        if current_picture_number is None: # 写真がない
                                            join_picture_damage_name = BridgePicture.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                            
                                            # print(f"join_picture_damage_name：{join_picture_damage_name}")
                                            if join_picture_damage_name.first():
                                                for picture in join_picture_damage_name:
                                                    if picture.damage_name:
                                                        # print(f"損傷名：{picture.damage_name}") # 損傷名
                                                        edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                                        new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                                        # 末尾のハイフン+任意の1文字を削除
                                                        damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                                        picture.memo = f"{picture.memo} / {parts_split},{damage_name}"
                                                    else:
                                                        picture.memo = f"{parts_split},{damage_name}"
                                                    picture.save()
                                                #print(join_picture_damage_name)
                                            #print("picture_number_boxのインデックスが範囲外です")
                                            continue
                                        # 「スペース + 2文字以上のアルファベット + 2文字以上の数字」にマッチする部分を捉える
                                        pattern = r'\s+[A-Za-z]{2,}[0-9]{2,}'
                                        # マッチした部分からアルファベット部分だけを削除するための関数を定義
                                        def remove_alphabets(match):
                                            # マッチした文字列からアルファベット部分を削除
                                            return re.sub(r'[A-Za-z]+', '', match.group())
                                            
                                        joined_picture_damage_name = FullReportData.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                        # print(f"joined_picture_damage_name：{joined_picture_damage_name}")
                                        
                                        loop_change = True
                                        for full_damaged_name in joined_picture_damage_name:
                                            if loop_change:
                                                print(full_damaged_name.join)
                                                loop_change = False
                                                
                                        # re.subでパターンにマッチする部分を編集
                                        edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                        new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                        damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                        existing_picture = BridgePicture.objects.filter(
                                            picture_number=current_picture_number,
                                            damage_coordinate_x=damage_coordinate_x,
                                            damage_coordinate_y=damage_coordinate_y,
                                            picture_coordinate_x=picture_coordinate_x,
                                            picture_coordinate_y=picture_coordinate_y,
                                            span_number=span_number,
                                            table=table,
                                            article=article,
                                            infra=infra
                                        ).first()
                                        
                                        if existing_picture is None:
                                            bridge_picture = BridgePicture(
                                                image=absolute_image_path,
                                                picture_number=current_picture_number,
                                                damage_name=damage_name,
                                                parts_split=edited_result_parts_name,
                                                memo=full_damaged_name.join,
                                                damage_coordinate_x=damage_coordinate_x,
                                                damage_coordinate_y=damage_coordinate_y,
                                                picture_coordinate_x=picture_coordinate_x,
                                                picture_coordinate_y=picture_coordinate_y,
                                                span_number=span_number,
                                                table=table,
                                                article=article,
                                                infra=infra
                                            )
                                            bridge_picture.save()
                                            picture_number_index += 1
                                    except FileNotFoundError:
                                        print(f"ファイルが見つかりません: {absolute_image_path}")
             
                        else:
                            update_fields['picture_number'] = ""
                    
                    report_data_exists = FullReportData.objects.filter(**update_fields).exists()
                    if report_data_exists:
                        print("データが存在しています。")
                    else:
                        try:
                            damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                            damage_obj.save()
                        except IntegrityError:
                            print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")
                        
            elif not is_multi_list(split_names) and not is_multi_list(damages) and damage_length >= 2: # かつ損傷名が2つ以上の場合
                picture_number_index = 0
                for name in split_names:
                    for damage in damages:
                        parts_name = name
                        pattern = r"(\d+)$"
                        # parts_nameからパターンにマッチする部分を検索
                        match = re.search(pattern, parts_name)
                        if match:
                            four_numbers = match.group(1)
                        else:
                            four_numbers = "00"
                        damage_name = flatten(damage)
                        # print(f"parts_name3:{parts_name}")
                        # print(f"damage_name3:{damage_name}")
                        parts_split = process_names(flatten(parts_name))
                        # print(f"this_time:{this_time_picture}")
                        list_in_picture = this_time_picture.split(",")
                        for single_picture in list_in_picture:
                            update_fields = {
                                'parts_name': parts_name,
                                'four_numbers': four_numbers,
                                'damage_name': damage_name,
                                'parts_split': parts_split,
                                'join': join,
                                'this_time_picture': single_picture,
                                'last_time_picture': last_time_picture,
                                'textarea_content': textarea_content,
                                'damage_coordinate_x': damage_coordinate_x,
                                'damage_coordinate_y': damage_coordinate_y,
                                'picture_coordinate_x': picture_coordinate_x,
                                'picture_coordinate_y': picture_coordinate_y,
                                'span_number': span_number,
                                'special_links': '/'.join([str(parts_split), str(damage_name), str(span_number)]),
                                'infra': infra,
                                'article': article,
                                'table': table
                            }
                        #print(f"径間番号:{span_number}")
                        # if FullReportData.objects.filter(join=join, this_time_picture=this_time_picture, span_number=span_number, table=table, damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y):
                            # update_fields['this_time_picture'] = ""
                            # update_fields['picture_number'] = ""
                            
                            if single_picture:
                                images = [single_picture]
                                update_fields['picture_number'] = picture_counter
                                picture_counter += 1
                                # BridgePictureモデルに保存
                                if numbers_only is not None and numbers_only != '':
                                    # print(f"images：{images}")
                                    for absolute_image_path in images:
                                        # print(f"absolute_image_path：{absolute_image_path}")
                                        try:
                                        # with open(absolute_image_path, 'rb') as image_file:
                                            #print(f"保存前：{numbers_only}")
                                            #print(f"オンリーナンバーズ（抽出後）: {picture_number_box}")
                                            if picture_number_index < len(picture_number_box):
                                                current_picture_number = picture_number_box[picture_number_index]
                                            else:
                                                current_picture_number = None
                                            # print(f"保存後：{current_picture_number}")
                                            # print("---------")
                                            if current_picture_number is None: # 写真がない
                                                join_picture_damage_name = BridgePicture.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                                # print(f"join_picture_damage_name：{join_picture_damage_name}")
                                                    
                                                if join_picture_damage_name.first():
                                                    for picture in join_picture_damage_name:
                                                        #print(picture)
                                                        if picture.damage_name:
                                                            # print(f"損傷名：{picture.damage_name}") # 損傷名
                                                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                                            # 末尾のハイフン+任意の1文字を削除
                                                            damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                                            picture.memo = f"{picture.memo} / {parts_split},{damage_name}"
                                                        else:
                                                            picture.memo = f"{parts_split},{damage_name}"
                                                        picture.save()
                                                    
                                                #print("picture_number_boxのインデックスが範囲外です")
                                                continue
                                            # 「スペース + 2文字以上のアルファベット + 2文字以上の数字」にマッチする部分を捉える
                                            pattern = r'\s+[A-Za-z]{2,}[0-9]{2,}'
                                            # マッチした部分からアルファベット部分だけを削除するための関数を定義
                                            def remove_alphabets(match):
                                                # マッチした文字列からアルファベット部分を削除
                                                return re.sub(r'[A-Za-z]+', '', match.group())
                                            
                                            joined_picture_damage_name = FullReportData.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                            # print(f"joined_picture_damage_name：{joined_picture_damage_name}")
                                            
                                            loop_change = True
                                            for full_damaged_name in joined_picture_damage_name:
                                                if loop_change:
                                                    # print(full_damaged_name.join)
                                                    loop_change = False
                                                    
                                            # re.subでパターンにマッチする部分を編集
                                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                            damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                            existing_picture = BridgePicture.objects.filter(
                                                picture_number=current_picture_number,
                                                damage_coordinate_x=damage_coordinate_x,
                                                damage_coordinate_y=damage_coordinate_y,
                                                picture_coordinate_x=picture_coordinate_x,
                                                picture_coordinate_y=picture_coordinate_y,
                                                span_number=span_number,
                                                table=table,
                                                article=article,
                                                infra=infra
                                            ).first()
                                            
                                            if existing_picture is None:
                                                bridge_picture = BridgePicture(
                                                    image=absolute_image_path,
                                                    picture_number=current_picture_number,
                                                    damage_name=damage_name,
                                                    parts_split=edited_result_parts_name,
                                                    memo=full_damaged_name.join,
                                                    damage_coordinate_x=damage_coordinate_x,
                                                    damage_coordinate_y=damage_coordinate_y,
                                                    picture_coordinate_x=picture_coordinate_x,
                                                    picture_coordinate_y=picture_coordinate_y,
                                                    span_number=span_number,
                                                    table=table,
                                                    article=article,
                                                    infra=infra
                                                )
                                                bridge_picture.save()
                                                picture_number_index += 1
                                        except FileNotFoundError:
                                            print(f"ファイルが見つかりません: {absolute_image_path}")
                      
                            else:
                                update_fields['picture_number'] = ""
                            
                        report_data_exists = FullReportData.objects.filter(**update_fields).exists()
                        if report_data_exists:
                            print("データが存在しています。")
                        else:
                            try:
                                damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                                damage_obj.save()
                            except IntegrityError:
                                print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")
                                 
        else: # 多重リストの場合
            picture_number_index = 0
            for i in range(name_length):
                for name in split_names[i]:
                    for damage in damages[i]:
                        parts_name = name
                        
                        pattern = r"(\d+)$"
                        match = re.search(pattern, parts_name)
                        if match:
                            four_numbers = match.group(1)
                        else:
                            four_numbers = "00"
                        original_damage_name = flatten(damage)
                        # print(f"parts_name4:{parts_name}")
                        # print(f"damage_name4:{original_damage_name}")
                        parts_split = process_names(flatten(parts_name))
                        # print(f"this_time:{this_time_picture}")
                        list_in_picture = this_time_picture.split(",")
                        picture_number_index = 0 # インデックス番号のリセット
                        for single_picture in list_in_picture:
                            update_fields = {
                                'parts_name': parts_name,
                                'four_numbers': four_numbers,
                                'damage_name': str(original_damage_name),
                                'parts_split': parts_split,
                                'join': join,
                                'this_time_picture': single_picture.strip(),
                                'last_time_picture': last_time_picture,
                                'textarea_content': textarea_content,
                                'damage_coordinate_x': damage_coordinate_x,
                                'damage_coordinate_y': damage_coordinate_y,
                                'picture_coordinate_x': picture_coordinate_x,
                                'picture_coordinate_y': picture_coordinate_y,
                                'span_number': span_number,
                                'special_links': '/'.join([str(parts_split), str(original_damage_name), str(span_number)]),
                                'infra': infra,
                                'article': article,
                                'table': table
                            }
                            # print(f"update_fields：{update_fields}")
                            
                            # この部分で今生成したupdate_fieldsでデータを保存または更新します
                            report_data_exists = FullReportData.objects.filter(**update_fields).exists()
                            if report_data_exists:
                                print("データが既に存在しています。")
                            else:
                                try:
                                    damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                                    damage_obj.save()
                                except IntegrityError:
                                    print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")
                            
                            if single_picture:
                                images = [single_picture]
                                update_fields['picture_number'] = picture_counter
                                picture_counter += 1
                                # BridgePictureモデルに保存
                                if numbers_only is not None and numbers_only != '':
                                    # print(f"images：{images}")
                                    for absolute_image_path in images:
                                        # print(f"absolute_image_path：{absolute_image_path}")
                                        try:
                                        # with open(absolute_image_path, 'rb') as image_file:
                                            #print(f"保存前：{numbers_only}")
                                            #print(f"オンリーナンバーズ（抽出後）: {picture_number_box}")
                                            
                                            # print(f"picture_number_index：{picture_number_index}") # 0/1
                                            # print(f"picture_number_box：{picture_number_box}") # ['10', '11']
                                            # print(f"len(picture_number_box)：{len(picture_number_box)}") # 2
                                            # print(f"picture_number_box[picture_number_index]：{picture_number_box[picture_number_index]}") # 10/11
                                            if picture_number_index < len(picture_number_box):
                                                current_picture_number = picture_number_box[picture_number_index]
                                            else:
                                                current_picture_number = None
                                                
                                            # print(f"保存後：{current_picture_number}")
                                            #print("---------")
                                            if current_picture_number is None: # 写真がない
                                                join_picture_damage_name = BridgePicture.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                                # print(f"join_picture_damage_name：{join_picture_damage_name}")
                                                if join_picture_damage_name.first():
                                                    for picture in join_picture_damage_name:
                                                        # print(picture)
                                                        if picture.damage_name:
                                                            # print(f"損傷名：{picture.damage_name}") # 損傷名
                                                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', original_damage_name)
                                                            # 末尾のハイフン+任意の1文字を削除
                                                            damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                                            picture.memo = f"{picture.memo} / {parts_split},{damage_name}"
                                                        else:
                                                            picture.memo = f"{parts_split},{damage_name}"
                                                        picture.save()
                                                    #print(join_picture_damage_name)
                                                #print("picture_number_boxのインデックスが範囲外です")
                                                continue
                                            # 「スペース + 2文字以上のアルファベット + 2文字以上の数字」にマッチする部分を捉える
                                            pattern = r'\s+[A-Za-z]{2,}[0-9]{2,}'
                                            # マッチした部分からアルファベット部分だけを削除するための関数を定義
                                            def remove_alphabets(match):
                                                # マッチした文字列からアルファベット部分を削除
                                                return re.sub(r'[A-Za-z]+', '', match.group())
                                            joined_picture_damage_name = FullReportData.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
                                            # print(f"joined_picture_damage_name：{joined_picture_damage_name}")
                                            
                                            loop_change = True
                                            for full_damaged_name in joined_picture_damage_name:
                                                if loop_change:
                                                    print(full_damaged_name.join)
                                                    loop_change = False

                                            # re.subでパターンにマッチする部分を編集
                                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                            # print(f"original_damage_name:{original_damage_name}")
                                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', original_damage_name)
                                            # print(f"new_damage_name：{new_damage_name}")
                                            # damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                            # print(damage_name)
                                            existing_picture = BridgePicture.objects.filter(
                                                image=absolute_image_path,
                                                picture_number=current_picture_number,
                                                damage_coordinate_x=damage_coordinate_x,
                                                damage_coordinate_y=damage_coordinate_y,
                                                picture_coordinate_x=picture_coordinate_x,
                                                picture_coordinate_y=picture_coordinate_y,
                                                span_number=span_number,
                                                table=table,
                                                article=article,
                                                infra=infra
                                            ).first()
                                            # print(f"absolute_image_path：{absolute_image_path}") # 写真URL
                                            # print(f"current_picture_number：{current_picture_number}") # 10
                                            # print(f"data：{existing_picture}") # BridgePicture object (946)
                                            
                                            if existing_picture is None:
                                                try:
                                                    bridge_picture = BridgePicture(
                                                        image=absolute_image_path, 
                                                        picture_number=current_picture_number,
                                                        damage_name=original_damage_name,
                                                        parts_split=edited_result_parts_name,
                                                        memo=full_damaged_name.join,
                                                        damage_coordinate_x=damage_coordinate_x,
                                                        damage_coordinate_y=damage_coordinate_y,
                                                        picture_coordinate_x=picture_coordinate_x,
                                                        picture_coordinate_y=picture_coordinate_y,
                                                        span_number=span_number,
                                                        table=table,
                                                        article=article,
                                                        infra=infra
                                                    )
                                                    bridge_picture.save()
                                                except:
                                                    index = images.index(absolute_image_path)
                                                    if index +1 >= len(images):
                                                        index = len(images) -1
                                                    bridge_picture = BridgePicture(
                                                        image=images[index], 
                                                        picture_number=current_picture_number,
                                                        damage_name=original_damage_name,
                                                        parts_split=edited_result_parts_name,
                                                        memo=full_damaged_name.join,
                                                        damage_coordinate_x=damage_coordinate_x,
                                                        damage_coordinate_y=damage_coordinate_y,
                                                        picture_coordinate_x=picture_coordinate_x,
                                                        picture_coordinate_y=picture_coordinate_y,
                                                        span_number=span_number,
                                                        table=table,
                                                        article=article,
                                                        infra=infra
                                                    )
                                                    # print(f"image：{images[index]}")
                                                    try:
                                                        bridge_picture.save()
                                                    except:
                                                        print("保存失敗")
                                                # print(f"bridge_picture：{bridge_picture}")
                                                picture_number_index += 1
                                        except FileNotFoundError:
                                            print(f"ファイルが見つかりません: {absolute_image_path}")
                                    
                            else:
                                update_fields['picture_number'] = ""
                        
                        report_data_exists = FullReportData.objects.filter(**update_fields).exists()
                        if report_data_exists:
                            print("データが存在しています。")
                        else:
                            try:
                                damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                                damage_obj.save()
                            except IntegrityError:
                                print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")
                                
    """辞書型の多重リストをデータベースに登録(ここまで)"""

    if "search_title_text" in request.GET:
        # request.GET：検索URL（http://127.0.0.1:8000/article/1/infra/bridge_table/?search_title_text=1径間） 
        search_title_text = request.GET["search_title_text"]
        # 検索URL内のsearch_title_textの値（1径間）を取得する
    else:
        search_title_text = "1径間" # 検索URLにsearch_title_textがない場合
    second_search_title_text = "損傷図"

    bridges = FullReportData.objects.filter(infra=pk, span_number=search_title_text) # 径間で絞り込み
    # parts_name のカスタム順序リスト
    parts_order = ['主桁', '横桁', '床版', 'PC定着部', '橋台[胸壁]', '橋台[竪壁]', '橋台[翼壁]', '支承本体', '沓座モルタル', '防護柵', '地覆', '伸縮装置', '舗装', '排水ます', '排水管']
    damage_order = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳', '㉑', '㉒', '㉓', '㉔', '㉕', '㉖']

    grouped_data = []
    for key, group in groupby(bridges, key=attrgetter('join', 'damage_coordinate_x', 'damage_coordinate_y')):
        grouped_data.append(list(group))

    photo_grouped_data = []
    for pic_key, pic_group in groupby(bridges, key=attrgetter('this_time_picture', 'span_number')):
        photo_grouped_data.append(list(pic_group))
    
    buttons_count = int(table.infra.径間数) # 数値として扱う
    buttons = list(range(1, buttons_count + 1)) # For loopのためのリストを作成
    
    # range(一連の整数を作成):range(1からスタート, ストップ引数3 = 2 + 1) → [1, 2](ストップ引数は含まれない)
    print(buttons)
    
    print(f"ボタン:{Table.objects.filter(infra=pk)}")# ボタン:<QuerySet [<Table: Table object (1)>]>
        # クエリセットを使って対象のオブジェクトを取得
    table_object = Infra.objects.filter(id=pk).first()    
    print(f"橋梁番号:{table_object}")# ボタン:Table object (1)
    print(f"橋梁番号:{table_object.id}")
    article_pk = infra.article.id
    print(f"案件番号:{article_pk}") # 案件番号:1
    
    picture_data = [] # ここで毎回初期化されます
    for data in bridges:
        # クエリセットでフィルタリング
        matches = BridgePicture.objects.filter(
            picture_coordinate_x=data.picture_coordinate_x,
            picture_coordinate_y=data.picture_coordinate_y,
            span_number=data.span_number,
            table=data.table,
            infra=data.infra,
            article=data.article
        ).distinct()
        # picture_data.append({"full_report": data, "matches": matches})
        # matches の各要素に対して個別に処理

        # matches に QuerySet を含めるために新たに作成
        match_details = [
            {"id": match.picture_number, "other_field": match.image}
            for match in matches
        ]
            
        picture_data.append({"full_report": data, "matches": matches, "picture": match_details})

    # matchesのキーに基づき、picturesを交互に選択してユニークに
    matches_seen = {}
    for entry in picture_data:
        matches_key = tuple(entry['matches'].values_list('id', flat=True))
        if matches_key not in matches_seen:
            matches_seen[matches_key] = 0

        # インデックスに基づいて選択
        # print(matches_seen[matches_key])
        # print(len(entry['picture']))
        
        if len(entry['picture']) != 0:
            picture_index = matches_seen[matches_key] % len(entry['picture'])
            entry['picture'] = [entry['picture'][picture_index]]

            # 次に進める
            matches_seen[matches_key] += 1

    # print(f"写真重複チェック:{picture_data}")
    context = {'object': table_object, 'article_pk': article_pk, 'grouped_data': grouped_data, 'photo_grouped_data': photo_grouped_data, 'buttons': buttons, 'picture_data': picture_data}
    # 渡すデータ：　損傷データ　↑　　　       　   joinと損傷座標毎にグループ化したデータ　↑　　　　　　 写真毎にグループ化したデータ　↑ 　　       径間ボタン　↑
    # print(f"写真格納場所確認：{context}")
    # テンプレートをレンダリング
    return render(request, 'infra/bridge_table.html', context)

# << entity_extension 　　　　関数をdxf_file.py(別モジュール)に移動 >>

# << find_square_around_text 関数をdxf_file.py(別モジュール)に移動 >>

# << create_picturelist 　　 関数をtasks.py    (非同期処理) に移動 >>


def handle_uploaded_file(f):
    import os
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    
    fs = FileSystemStorage()
    filename = fs.save(f.name, f)
    print(f"filename：{filename}")
    folder_name = os.path.splitext(f.name)[0] # os.path.splittext：ファイルの拡張子を除いたベースネームを取得
    full_path = os.path.join(fs.location, filename)
    print(f"folder_name：{folder_name}")

    folder_name = os.path.dirname(full_path)
    print(f"folder_name：{folder_name}")
    return f'infra/img/{folder_name}/{filename}'
    # return os.path.join(settings.MEDIA_URL, filename)

# << 写真の変更内容を反映 >>
def upload_picture(request, article_pk, pk):
    if request.method == 'POST':
        action = request.POST.get('action')
        bridge_id = request.POST.get('bridgeId')
        bridge = get_object_or_404(FullReportData, id=bridge_id)
        print("写真帳の変更を行います")
        print(f"action：{action}")
        print(f"bridge_id：{bridge_id}")
        print(f"bridge：{bridge}")
        
        if action == 'change':
            old_picture_path = request.POST.get('oldPicturePath')
            new_picture_path = handle_uploaded_file(request.FILES['file'])
            bridge.this_time_picture = bridge.this_time_picture.replace(old_picture_path, new_picture_path)
            bridge.save()
            print("変更する動作")
            print(f"old_picture_path：{old_picture_path}")
            print(f"new_picture_path：{new_picture_path}")
            print(f"bridge.this_time_picture：{bridge.this_time_picture}")
            return JsonResponse({'success': True})

        elif action == 'add':
            new_picture_path = handle_uploaded_file(request.FILES['file'])
            if bridge.this_time_picture:
                bridge.this_time_picture += f', {new_picture_path}'
            else:
                bridge.this_time_picture = new_picture_path
            bridge.save()
            print("追加する動作")
            print(f"new_picture_path：{new_picture_path}")
            print(f"bridge.this_time_picture：{bridge.this_time_picture}")
            return JsonResponse({'success': True})

        elif action == 'delete':
            picture_path = request.POST.get('picturePath')
            pictures = bridge.this_time_picture.split(', ')
            pictures.remove(picture_path)
            bridge.this_time_picture = ', '.join(pictures) if pictures else None
            bridge.save()
            print("削除する動作")
            print(f"picture_path：{picture_path}")
            print(f"pictures：{pictures}")
            print(f"bridge.this_time_picture：{bridge.this_time_picture}")
            return JsonResponse({'success': True})

        return JsonResponse({'success': False})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



# << 所見一覧の作成 >>
def observations_list(request, article_pk, pk):
    context = {}
    print("所見ID確認")
    infra = Infra.objects.filter(id=pk).first()
    print(f"Infra:{infra}") # 旗揚げチェック(4)
    article = infra.article
    print(f"article:{article}") # お試し(2)
    table = Table.objects.filter(infra=infra.id, article=article.id).first()
    # table = Table.objects.filter(id=pk).first()
    print(f"table_name:{table}")

    bucket_name = 'infraprotect'
    print(bucket_name)
    folder_name = article.案件名+"/"
    print(folder_name)
    pattern = f'*{infra.title}*/{infra.title}.dxf'
    print(pattern)
    
    # 該当するオブジェクトを取得
    matched_objects = match_s3_objects_with_prefix(bucket_name, folder_name, pattern)

    if matched_objects:
        print(f"該当オブジェクト：{matched_objects}")
    else:
        print("ファイルが見つかりません")

    # 結果を表示
    for obj_key in matched_objects:
        encode_dxf_filename = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{obj_key}"
    
    dxf_filename = urllib.parse.quote(encode_dxf_filename, safe='/:') # スラッシュとコロン以外をエンコード

    print(f"dxfファイルのデコードURLは：{encode_dxf_filename}")
    print(f"dxfファイルの絶対URLは：{dxf_filename}")
    
    # URLから径間番号を取得
    if "search_title_text" in request.GET:
        search_title_text = request.GET["search_title_text"]
    else:
        search_title_text = "1径間"

    second_search_title_text = "損傷図"
    
    # sorted_items = create_picturelist(request, table, dxf_filename, search_title_text, second_search_title_text)
    """"""
    # 全パーツデータを取得

    infra_name = table.infra.title
    print(f"infra_name:{infra_name}")
    parts_data = PartsNumber.objects.filter(infra=pk)
    print(f"parts_data:{parts_data}")
    
    article = Article.objects.filter(id=article_pk).first()
    infra = Infra.objects.filter(id=pk).first()
    table = Table.objects.filter(infra=pk).first()    
    
    material_replace_map = {
        "鋼": "S",
        "コンクリート": "C",
        "アスファルト": "A",
        "ゴム": "R",
        "その他": "X",
    }
    
    number_change = {
        '①': '腐食',
        '②': '亀裂',
        '③': 'ゆるみ・脱落',
        '④': '破断',
        '⑤': '防食機能の劣化',
        '⑥': 'ひびわれ',
        '⑦': '剥離・鉄筋露出',
        '⑧': '漏水・遊離石灰',
        '⑨': '抜け落ち',
        '⑩': '補修・補強材の損傷',
        '⑪': '床版ひびわれ',
        '⑫': 'うき',
        '⑬': '遊間の異常',
        '⑭': '路面の凹凸',
        '⑮': '舗装の異常',
        '⑯': '支承部の機能障害',
        '⑰': 'その他',
        '⑱': '定着部の異常',
        '⑲': '変色・劣化',
        '⑳': '漏水・滞水',
        '㉑': '異常な音・振動',
        '㉒': '異常なたわみ',
        '㉓': '変形・欠損',
        '㉔': '土砂詰まり',
        '㉕': '沈下・移動・傾斜',
        '㉖': '洗掘',
    }
    
    lank_order = ['a', 'b', 'c', 'd', 'e']  # ランクの順序をリストで定義
    def get_lank_value(damage_name):
        """damage_nameのランク部分を取得する"""
        if "-" in damage_name:
            return damage_name.split('-')[-1]
        return None
    
    # FullReportDataの準備
    damage_comments = defaultdict(lambda: {'damage_lanks': [], 'this_time_pictures': []})

    for part in parts_data:
        part_full_name = f"{part.parts_name} {part.symbol}{part.number}"
        span_number = part.span_number + '径間'
        print(f"partデータのarticle：{part.article}")

        # FullReportDataから該当するデータを取得
        report_data_list = FullReportData.objects.filter(
            parts_name=part_full_name, # FullReportDataのparts_nameオブジェクトがpart_full_name(主桁 Mg0101)と同じ、かつ
            span_number=span_number, # FullReportDataのspan_numberオブジェクトがspan_number(1径間)と同じ、かつ
            infra=part.infra, # FullReportDataのinfraオブジェクトがpart.infraと同じ場合
            article=part.article
        )  

        for report_data in report_data_list:
            print(f"report_data_list:{report_data.damage_name}")
            print(f"picture:{report_data.this_time_picture}")

            damage_list_material = "" # 空のdamage_list_materialを用意
            for m in part.material.all(): # part.materialの全データを取得し「m」変数に入れる
                damage_list_material += m.材料 + "," # 「m」の材料フィールドを指定してdamage_list_materialに入れる
                
            elements = damage_list_material.split(',')
            replaced_elements = [material_replace_map.get(element, element) for element in elements] # それぞれの要素を置換辞書に基づいて変換します
            damage_list_materials = ','.join(replaced_elements) # カンマで結合します。
            
            damage_name = report_data.damage_name.split('-')[0] if '-' in report_data.damage_name else report_data.damage_name
            if damage_name == "NON":
                damage_name = damage_name
            elif damage_name[0] != '⑰':
                damage_name = number_change[damage_name[0]]
            else:
                damage_name = damage_name[1:] # ⑦剥離・鉄筋露出から先頭の一文字を省く
                
            damage_lank = report_data.damage_name.split('-')[1] if '-' in report_data.damage_name else report_data.damage_name
            
            # DamageListに必要なフィールドを含むインスタンスを作成
            # << 損傷一覧(Excel)用データ登録 >>
            damage_list_entry = DamageList(
                parts_name = part.parts_name, # 主桁
                symbol = part.symbol, # Mg
                number = part.number, # 0101
                material = damage_list_materials[:-1], # 最後のコンマが不要なため[-1:]（S,C）
                main_parts = "〇" if part.main_frame else "", # 主要部材のフラグ
                damage_name = damage_name, # 剥離・鉄筋露出
                damage_lank = damage_lank, # d
                span_number = part.span_number,
                infra = part.infra,
                article = part.article
            )

            try:
                # DamageListインスタンスを保存
                damage_list_entry.save()
                
            except IntegrityError:
                # 重複データがある場合の処理
                print("データが存在しています。")
                # 必要に応じてログを記録したり、他の処理を追加したりできます
                # continue  # 次のループに進む
            
    """所見用のクラス登録"""
    damage_comments = defaultdict(lambda: {'damage_lanks': [], 'this_time_pictures': []})

    for part in parts_data:
        part_full_name = f"{part.parts_name} {part.symbol}{part.number}"
        span_number = part.span_number + '径間'

        report_data_list = FullReportData.objects.filter(
            parts_name=part_full_name,
            span_number=span_number,
            infra=part.infra,
            article=part.article
        )

        for report_data in report_data_list:
            main_parts_list_left = ["主桁", "PC定着部"]
            main_parts_list_right = ["横桁", "橋台"]
            main_parts_list_zero = ["床版"]

            parts_name = f"{part.parts_name} {part.number}"

            if any(word in parts_name for word in main_parts_list_left): # main_parts_list_leftリストと一致した場合
                left = parts_name.find(" ")
                number2 = parts_name[left+1:]
                number_part = re.search(r'[A-Za-z]*(\d+)', number2).group(1)
                result_parts_name = parts_name[:left] + " " + number_part[:2]
            elif any(word in parts_name for word in main_parts_list_right): # main_parts_list_rightリストと一致した場合
                right = parts_name.find(" ")
                number2 = parts_name[right+1:]
                number_part = re.search(r'[A-Za-z]*(\d+)', number2).group(1)
                result_parts_name = parts_name[:right] + " " + number_part[2:] if len(number_part) < 5 else number_part[2:]
            elif any(word in parts_name for word in main_parts_list_zero): # main_parts_list_zeroリストと一致した場合
                right = parts_name.find(" ")
                result_parts_name = parts_name[:right] + " 00"
            else:
                right = parts_name.find(" ")
                result_parts_name = parts_name[:right]

            damage_name = report_data.damage_name.split('-')[0] if '-' in report_data.damage_name else report_data.damage_name
            if damage_name == "NON":
                damage_name = damage_name
            elif damage_name[0] != '⑰':
                damage_name = number_change[damage_name[0]]
            else:
                damage_name = damage_name[1:] 
            damage_lank = report_data.damage_name.split('-')[1] if '-' in report_data.damage_name else report_data.damage_name    
            # 部材名と損傷名の組み合わせでデータを作成
            damage_comments[(result_parts_name, damage_name)]['damage_lanks'].append(damage_lank)
            damage_comments[(result_parts_name, damage_name)]['this_time_pictures'].append(report_data.this_time_picture)
            
            damage_comment_material = ""
            for m in part.material.all():
                damage_comment_material += m.材料 + ","
            elements = damage_comment_material.split(',')
            replaced_elements = [material_replace_map.get(element, element) for element in elements]
            damage_comment_materials = ','.join(replaced_elements)
            print(f"replaced_elements:{replaced_elements}")
            print(f"damage_comment_materials:{damage_comment_materials}")

            damage_comments[(result_parts_name, damage_name)]['material'] = damage_comment_materials[:-1]
            damage_comments[(result_parts_name, damage_name)]['main_parts'] = "〇" if part.main_frame else ""
            damage_comments[(result_parts_name, damage_name)]['span_number'] = part.span_number
            damage_comments[(result_parts_name, damage_name)]['infra'] = part.infra
            damage_comments[(result_parts_name, damage_name)]['article'] = part.article

    for (result_parts_name, damage_name), data in damage_comments.items():
        print("1571行目")
        damage_lanks = data['damage_lanks']
        damage_max_lank = max(damage_lanks)
        damage_min_lank = min(damage_lanks)
        
        start_comma_pictures = ','.join(str(picture) for picture in set(data['this_time_pictures']) if picture is not None) # 重複なし
        # double_comma_picturesにデフォルト値を設定
        double_comma_pictures = start_comma_pictures
        
        if start_comma_pictures.startswith(","):
            double_comma_pictures = start_comma_pictures[1:]
        before_combined_pictures = double_comma_pictures.replace(",,", ",")
        print(f"before_combined_pictures：{before_combined_pictures}")

        # << 管理サイトに登録するコード（所見） >>
        try:
            damage_comment_entry, created = DamageComment.objects.get_or_create(
                parts_name=result_parts_name,
                damage_name=damage_name,
                span_number=data['span_number'],
                infra=data['infra'],
                article=data['article'],
                defaults={
                    'material': data['material'],
                    'main_parts': data['main_parts'],
                    'damage_max_lank': damage_max_lank,
                    'damage_min_lank': damage_min_lank,
                    'this_time_picture': before_combined_pictures
                }
            )
            if not created:
                # 既存データが見つかった場合には、フィールド値を更新
                damage_comment_entry.material = data['material']
                damage_comment_entry.main_parts = data['main_parts']
                damage_comment_entry.damage_max_lank = damage_max_lank
                damage_comment_entry.damage_min_lank = damage_min_lank
                damage_comment_entry.this_time_picture = before_combined_pictures
                damage_comment_entry.save()

        except IntegrityError:
            # 重複データがある場合の処理
            print("データが存在しています。")
            # 必要に応じてログを記録したり、他の処理を追加したりできます
            continue  # 次のループに進む
        
        # BridgePictureからのimageを取得し、damage_comment_entryに追加する
        bridge_pictures = BridgePicture.objects.filter(
            memo__contains=f"{result_parts_name},{damage_name}", # __contains：部分一致
            span_number=f"{data['span_number']}径間",
            infra=data['infra'],
            article=data['article']
        )

        images = []        
        def remove_unwanted_prefix(text):
            # 「https:/」を探して、それ以前の部分を削除する
            parts = text.split('https:/', 1)
            if len(parts) > 1:
                return 'https:/' + parts[1]
            else:
                return None

        for picture in bridge_pictures:
            decoded_url = unquote(picture.image.url)
            print(f"写真パス：{decoded_url}")
            images.append(decoded_url)
            # images.append(remove_unwanted_prefix(decoded_url))
            print(picture)

        damage_comment_entry.images = images
           
    # span_numberの順かつ、replace_nameの順かつ、parts_numberの順かつ、numberの順に並び替え 
    sorted_data = DamageComment.objects.filter(infra=pk).order_by('span_number', 'replace_name', 'parts_number', 'number')
    
    if "search_title_text" in request.GET:
        search_title_text = request.GET["search_title_text"]

    else:
        search_title_text = "1径間"
    
    span_create_number = search_title_text.replace("径間", "")
    print(span_create_number)
    filtered_bridges = DamageComment.objects.filter(infra=pk, span_number=span_create_number).order_by('span_number', 'replace_name', 'parts_number', 'number')
    print(f"bridges:{filtered_bridges}")
    buttons_count = int(table.infra.径間数) # 数値として扱う
    buttons = list(range(1, buttons_count + 1)) # For loopのためのリストを作成
    # range(一連の整数を作成):range(1からスタート, ストップ引数3 = 2 + 1) → [1, 2](ストップ引数は含まれない)
    print(buttons)

    # print(f"所見ボタン:{DamageComment.objects.filter(infra=pk)}")# ボタン:<QuerySet [<Table: Table object (15)>]>
    # print(f"所見ボタン:{DamageComment.objects.filter(infra=pk).first()}")# ボタン:Table object (18)(QuerySetのままだとうまく動作しない)
    #   1(径間)  ,      1(主桁)  ,        01     ,    6(ひびわれ)

    # print("所見引き渡しID確認")
    infra = Infra.objects.filter(id=pk).first()
    article = infra.article
    observer_object = infra
    
    images_url = [] # ここで毎回初期化されます
    for observer_data in filtered_bridges:
        print(f"損傷名：{observer_data.damage_name}")
        
        pattern = r'^[①-㉖]|-[a-zA-Z]$'
        damage_name_result = re.sub(pattern, '', observer_data.damage_name)
        print(observer_data.parts_name)
        print(damage_name_result)
        print(observer_data.span_number)
        print(observer_data.infra)
        print(observer_data.article)
        
        span_number_data = observer_data.span_number + "径間"
        # クエリセットでフィルタリング
        matches = BridgePicture.objects.filter( # 部材名/部材番号/損傷名/径間名/案件名/橋梁名
            parts_split=observer_data.parts_name, # 主桁 01
            damage_name__icontains=damage_name_result,  # __icontainsを使用すると、部分一致で検索 # ⑦剥離・鉄筋露出-e
            span_number=span_number_data, # 1径間/1
            infra=observer_data.infra,
            article=observer_data.article
        ).distinct()
        
        match_details = [
            {"id": match.picture_number, "other_field": match.image}
            for match in matches
        ]
            
        images_url.append({"full_report": observer_data, "matches": matches, "match_details": match_details})
        
    context = {'object': observer_object, 'article_pk': article_pk, 'data': filtered_bridges, 'article_pk': article_pk, 'pk': pk, 'buttons': buttons, 'images': images_url}
    print(f"所見用context：{context}")
    return render(request, 'infra/observer_list.html', context)


# << 所見コメントのリアルタイム保存 >>
def damage_comment_edit(request, pk):
    if request.method == "POST":
        # TODO: 編集を受け付ける
        # DamageComment の idを受け取る。
        # URL：path('damage_comment_edit/<int:pk>/', views.damage_comment_edit , name="damage_comment_edit")
        damage_comment = DamageComment.objects.get(id=pk) # idが同じDamageCommentデータを取得(int:pk 1種類のidが必要)
        print(damage_comment)
        form = DamageCommentEditForm(request.POST, instance=damage_comment)
     # ユーザーが送信したPOSTデータをFormに渡す ↑　　　　　　　　↑ 編集するオブジェクト
        print("編集します。")

        if form.is_valid(): # バリデーション
            form.save()
            print("編集保存完了")
        else:
            print(form.errors)
        # リダイレクト処理  　　　　　　　　　　　　　↓　damage_commentクラス → infraフィールド(infraクラスに移る) → articleフィールド(articleクラスに移る)からarticle.idを取得
        return redirect("observations-list", damage_comment.infra.article.id, damage_comment.infra.id )
    
    
# << どの対策区分ボタンが押されたか、管理サイトに保存 >>
def damage_comment_jadgement_edit(request, pk):
    if request.method == "POST":
        #TODO: 編集を受け付ける。
        # DamageComment の idを受け取る。
        print("DamageCommentJadgementEditForm 発動。")
        damage_comment = DamageComment.objects.get(id=pk)
        form = DamageCommentJadgementEditForm(request.POST, instance=damage_comment)
        
        if form.is_valid():
            form.save()
            print("編集保存完了")
        else:
            print(form.errors)

        return redirect("observations-list", damage_comment.infra.article.id, damage_comment.infra.id )
    
# << どの損傷原因ボタンが押されたか、管理サイトに保存 >>
def damage_comment_cause_edit(request, pk):
    if request.method == "POST":
        #TODO: 編集を受け付ける。
        # DamageComment の idを受け取る。
        print("DamageCommentCauseEditForm 発動。")
        damage_comment_cause = DamageComment.objects.get(id=pk)
        form = DamageCommentCauseEditForm(request.POST, instance=damage_comment_cause)
        
        if form.is_valid():
            form.save()
            print("編集保存完了")
        else:
            print(form.errors)

        return redirect("observations-list", damage_comment_cause.infra.article.id, damage_comment_cause.infra.id )
    
# << 管理サイトに登録したデータをエクセルに出力 >>