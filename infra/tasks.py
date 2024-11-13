from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch
from functools import lru_cache, reduce
import glob
import re
import time

import boto3
import urllib

from markupsafe import Markup
from infra.dxf_file import find_square_around_text
from infra.models import NameEntry
from infra.picture_damages_memo import format_damages, process_damage, process_related_damages

# 名前の置換関数をループの外で定義
def get_sorted_replacements(article_id):
    name_entries = NameEntry.objects.filter(article=article_id)
    replacements = [(entry.alphabet, entry.name) for entry in name_entries] + [(" ", "　")]
    return sorted(replacements, key=lambda x: len(x[0]), reverse=True)

# << 損傷写真帳に渡すためのデータをリスト化 >>
def create_picturelist(request, table, dxf_filename, search_title_text, second_search_title_text):
    print("関数スタート：create_picturelist")
    #                                                                                              1径間　　　　　  　　　　損傷図
    extracted_text = find_square_around_text(table.article.id, table.infra.id, dxf_filename, search_title_text, second_search_title_text)
    # find_square_around_text関数の結果をextracted_text変数に格納
    print("関数スタート：find_square_around_text")
    # リストを処理して、スペースを追加する関数を定義
    def add_spaces(text):
        # 正規表現でアルファベットと数字の間にスペースを挿入
        return re.sub(r'(?<! )([a-zA-Z]+)(\d{2,})', r' \1\2', text)

    # 変更されたリストを保存するための新しいリスト
    new_extracted_text = []

    # 各サブリストを処理
    for sub_extracted_text in extracted_text:
        # 先頭の文字列を修正
        if " " not in sub_extracted_text[0]:
            sub_extracted_text[0] = add_spaces(sub_extracted_text[0])
        # 新しいリストに追加
        new_extracted_text.append(sub_extracted_text)

    extracted_text = new_extracted_text

    for index, data in enumerate(extracted_text):
        # 最終項目-1まで評価
        if index < (len(extracted_text) -1):
            # 次の位置の要素を取得
            next_data = extracted_text[index + 1]
            # 特定の条件(以下例だと、１要素目が文字s1,s2,s3から始まる）に合致するかチェック
            if ("月" in next_data[0] and "日" in next_data[0]) or ("/" in next_data[0]) and (re.search(r"[A-Z]", next_data[0], re.IGNORECASE) and re.search(r"[0-9]", next_data[0])):
                # 合致する場合現在の位置に次の要素を併合 and "\n" in cad
                data.extend(next_data)
                # 次の位置の要素を削除
                extracted_text.remove(next_data)
    # extracted_text = [['主桁 Mg0101', '①-d', '写真番号-00', 'defpoints'], ['主桁 Mg0902', '⑦-c', '写真番号-00', 'defpoints']]
    print("位置要素を取得")
# ↓　インデックスを1つ左に移動した(return sorted_items以外)
    # それぞれのリストから文字列のみを抽出する関数(座標以外を抽出)
    def extract_text(data):
        extracted = []  # 空のリストを用意
        removed_elements = []  # バックアップ用リスト

        pattern = r'[\u2460-\u3256]'  # ⓵～㉖

        for list_item in data:  # list_item変数に要素を代入してループ処理
            # print(list_item)
            item_extracted = [item for item in list_item if isinstance(item, str)]
            
            if item_extracted:  # item_extractedが空でないことを確認
                # 最後の要素に特定の文字が含まれているかどうかをチェック
                contains_symbols = bool(re.search(pattern, item_extracted[-1]))

                # '月'と'日'が最後の要素に含まれているかどうかをチェック
                if '月' in item_extracted[-1] and '日' in item_extracted[-1] and not contains_symbols:
                    extracted.append(item_extracted[:-2])
                    # 座標や日時を削除し、removed_elementsに保存
                    removed_elements.append([item for item in list_item if item not in item_extracted[:-2]])
                else:
                    extracted.append(item_extracted)
                    # 座標や日時を削除し、removed_elementsに保存
                    removed_elements.append([item for item in list_item if item not in item_extracted])
            else:
                extracted.append([])
                removed_elements.append(list_item)

        return extracted, removed_elements  # extractedの結果を関数に返す

    # 関数を使って特定の部分を抽出
    extracted_text, removed_elements = extract_text(extracted_text)
    print("特定の要素を抽出")
    
    first_item = []
    current_detail = None  # 現在処理しているdetailを追跡

    for text, removed in zip(extracted_text, removed_elements):  # 1つずつのリスト
        result_list = []
        for item in text:# 1つずつの要素
        # 各条件を個別に確認する
            space_exists = re.search(r"\s+", item) is not None # スペースを含む
            alpha_exists = re.search(r"[a-zA-Z]+", item) is not None # アルファベットを含む
            digits_exists = re.search(r"\d{2,}", item) is not None # 2桁以上の数字を含む
        
            if space_exists and alpha_exists and digits_exists:
            # 新しいdetail項目を作成し、resultsに追加します
                current_detail = {'detail': item, 'items': []}
                result_list.append(current_detail)
            
            else:
            # 既存のdetailのitemsに現在の項目を追加
                if current_detail is not None:
                    current_detail['items'].append(item)
                
    # 元の要素を結果に追加
        for elem in removed:
            result_list.append(elem)

    #print(result_list)
        first_item.append(result_list)
    
    print(f"first_item：{first_item}")
    extracted_text = first_item
        
    sub_first_item = [] 
    for check_sub_list in extracted_text:
        first_sub_item = []
        for first_sub_list in check_sub_list:
            # 各条件を個別に確認する
            space_exists = re.search(r"\s+", str(first_sub_list)) is not None # スペースを含む
            alpha_exists = re.search(r"[a-zA-Z]+", str(first_sub_list)) is not None # アルファベットを含む
            digits_exists = re.search(r"\d{2,}", str(first_sub_list)) is not None # 2桁以上の数字を含む
            # 正規表現を使って、コンマの直後に数字以外の文字が続く場所を見つけます。
            pattern = re.compile(r',(?![0-9])')
            # print(sub_list)
    # リスト内包表記で各要素をチェックして、条件に合致する場合は置き換えを行います。
            if space_exists and alpha_exists and digits_exists and not "月" in first_sub_list:
                # sub_list自体を文字列に変換するのではなく、detailフィールドのみを操作する
                detail_str = first_sub_list['detail']
                # detail_strのカンマの直後に`</br>`タグを挿入
                processed_str = pattern.sub(",", detail_str)
                # processed_strをMarkup関数を使ってHTML安全なマークアップに変換
                markup_str = Markup(processed_str)
                # markup_strをリストに包む
                wrapped_markup_str = [markup_str]
                # first_sub_itemリストに追加
                first_sub_item.append(wrapped_markup_str)
        sub_first_item.append(first_sub_item)
    # [[[Markup('横桁 Cr0503')]], [[Markup('主桁 Mg0110')], [Markup('床版 Ds0101')]], [[Markup('横桁 Cr0802')]], [[Markup('排水ます Dr0102,0201')]], [[Markup('排水ます Dr0202')]], [[Markup('PC定着部 Cn1101')]], [[Markup('排水ます Dr0102,0201,0202')]]]
        print("sub_first_itemの作成")
        def process_item(item):
            if isinstance(item, Markup):
                item = str(item)
            
            if ',' in item:
                sub_items = item.split(',')
                for i, sitem in enumerate(sub_items):
                    if i > 0 and sitem[0].isnumeric():
                        before_sub_item = sub_items[i - 1]
                        before_sub_item_splitted = before_sub_item.split()
                        before_sub_item_prefix = before_sub_item_splitted[0]
                        before_sub_item_suffix = ''
                        
                        for char in before_sub_item_splitted[1]:
                            if char.isnumeric():
                                break
                            else:
                                before_sub_item_suffix += char
                        
                        sub_items[i] = before_sub_item_prefix + ' ' + before_sub_item_suffix + sitem
                item = ",".join(sub_items)
            
            return item.split(',')

        first_item = []
        for sub_one in sub_first_item:
            append2 = []
            for text_items in sub_one:
                result_items = []
                for item in text_items:
                    processed_items = process_item(item)
                    result_items.extend(processed_items)
                append2.append(result_items)
            first_item.append(append2)

    # << ◆損傷種類(second)の要素◆ >> 
    # リストの各要素から記号を削除する関数
    def remove_symbols(other_items):
        symbols = ['!', '[', ']', "'"]

        processed_other_items = []
        for item in other_items:
            processed_item = ''.join(c for c in item if c not in symbols)
            processed_other_items.append(processed_item)

        return processed_other_items
    
    # それ以外の要素(損傷名)を抽出
    pattern = r'[\u2460-\u2473\u3251-\u3256].*-[a-zA-Z]' # 丸数字とワイルドカードとアルファベット
    second_items = []
    for second_sub_list in extracted_text:
        filtered_sub_list = []
        for damage_item in second_sub_list:
            if 'items' in damage_item:
            # sub_list自体を文字列に変換するのではなく、detailフィールドのみを操作する
                detail_damage = damage_item['items']
                for split_detail_damage in detail_damage:
                    if "," in split_detail_damage:
                        join_detail_damage = ""
                        middle_damage = split_detail_damage.split(",")
                        join_detail_damage = middle_damage
                    else:
                        join_detail_damage = detail_damage
                        
                filtered_sub_list.append(join_detail_damage)
        second_items.append(filtered_sub_list)

    third_items = []
    bottom_item = []
    damage_coordinate = []
    picture_coordinate = []
    for other_sub_list in extracted_text:
        list_count = sum(isinstance(item, list) for item in other_sub_list) # リストの中にリストがいくつあるか数える
        
        if list_count == 2: # 座標が2つのとき=Defpointsが存在するとき
            bottom_item.append(other_sub_list[-3]) # 最後から3番目の要素を抽出（写真番号-00）
            third_items.append(other_sub_list[-4]) # 最後から4番目の要素を抽出（Defpoints）
            damage_coordinate.append(other_sub_list[-2])
            picture_coordinate.append(other_sub_list[-1])
        else: # Defpointsがない時
            bottom_item.append("") # bottom:写真番号なし
            third_items.append(None) # third:Defpointsなし
            damage_coordinate.append(other_sub_list[-1]) # damage:
            picture_coordinate.append(None) # picture:写真指定なし
    #print(other_sub_list)
    # print("~~~~~~~~~~~")
    # print(bottom_item)
    result_items = []# 配列を作成
    for item in bottom_item:# text_itemsの要素を1つずつitem変数に入れてforループする
        # print("～～～")
        # print(f"データ確認：{item}")
        if isinstance(item, str) and ',' in item:# 要素が文字列で中にカンマが含まれている場合に実行
            pattern = r',(?![^(]*\))'
            sub_items = re.split(pattern, item)# カンマが含まれている場合カンマで分割
            extracted_item = []# 配列を作成
            
            for sub_item in sub_items:# bottom_itemの要素を1つずつitem変数に入れてforループする
                len_sub_item = len(sub_item)
                for p in range(len_sub_item):#itemの文字数をiに代入
                    if "A" <= sub_item[p].upper() <= "Z" and p < len_sub_item - 1 and sub_item[p+1].isnumeric():#i文字目がアルファベットかつ、次の文字が数字の場合
                        extracted_item.append(sub_item[:p+1]+"*/*"+sub_item[p+1:])# アルファベットと数字の間に*/*を入れてextracted_itemに代入
                        break
            join = ",".join(extracted_item)# 加工した内容をカンマ区切りの１つの文字列に戻す
            result_items.append(join)# result_itemsに格納

        elif isinstance(item, str) or ',' in item:  # 要素が文字列でカンマを含まない場合
            non_extracted_item = ''  # 変数のリセット
            len_range_item = len(item)
            for j in range(len_range_item):
                if "A" <= item[j].upper() <= "Z" and j < len_range_item - 1 and item[j+1].isnumeric():#i文字目がアルファベットかつ、次の文字が数字の場合
                    non_extracted_item = item[:j+1]+"*/*"+item[j+1:]#アルファベットまでをextracted_itemに代入
                elif non_extracted_item == '':
                    non_extracted_item = item
            result_items.append(non_extracted_item)
        else:
            result_items.append(item)

    def remove_parentheses_from_list(last):
        pattern = re.compile(r"\([^()]*\)")
        result = [pattern.sub("", string) for string in last]
        return result

    last_item = remove_parentheses_from_list(result_items)

    damage_table = []
    len_first_item = len(first_item)
    
    for i in range(len_first_item):
        start3 = time.time()
        try:
            third = third_items[i]
        except IndexError:
            third = None
        
        # ['NON-a', '9月7日 S404', '9月7日 S537', '9月8日 S117,9月8日 S253']
        if len(last_item)-1 < i:
            break

        if not isinstance(last_item[i], list):
            sorted_replacements = get_sorted_replacements(table.article.id)
            name_item = reduce(lambda acc, pair: acc.replace(pair[0], pair[1]), sorted_replacements, last_item[i])

        pattern = r',(?![^(]*\))'
        dis_items = re.split(pattern, name_item)
        
        time_result = []
        current_date = ''  # 現在の日付を保持する変数
        for time_item in dis_items:
            #print(f"このデータは：{time_item}")
            # 先頭が数字で始まるかチェック（日付として扱えるか）
            if re.match(r'^\d', time_item):
                current_date = re.match(r'^\d+月\d+日', time_item).group(0)  # 日付を更新
                time_result.append(time_item)  # 日付がある項目はそのまま追加
            else:
                # 日付がない項目は、現在の日付を先頭に追加
                time_result.append(''.join([current_date, '　', time_item]))

        name_and_wildcardnumber = [item + ".jpg" for item in time_result]
        # ['9月8日 佐藤*/*117.jpg', '9月8日 佐藤*/*253.jpg']
        print("写真の検索にかかった時間_time3: ", time.time() - start3 )
        
        # << S3にアップロードした写真のワイルドカード検索 >>
        start4 = time.time()
        s3 = boto3.client('s3')

        bucket_name = 'intection' # infraprojectから変更(リージョンの変更)
        article_folder_name = table.article.案件名
        infra_folder_name = table.infra.title

        pattern = r'\(.*?\)|\.jpg|\*'  # カッコとその中・「.jpg」・「*」を削除
        split_wildcard_lists = [re.split(r'[,/]', re.sub(pattern, '', item)) for item in name_and_wildcardnumber]

        s3_folder_name = [f"{article_folder_name}/{infra_folder_name}/{item[0]}/" for item in split_wildcard_lists if len(item) >= 1]
        wildcard_picture = tuple(item[1] for item in split_wildcard_lists if len(item) >= 2)  # ('117', '253')

        @lru_cache(maxsize=None)
        def search_s3_objects(bucket, prefix, pattern):
            paginate = s3.get_paginator("list_objects_v2")
            matching_keys = []

            for page in paginate.paginate(Bucket=bucket, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if fnmatch.fnmatch(key, f"{prefix}*{pattern}.jpg"):
                            matching_keys.append(key)
            return matching_keys

        sub_dis_items = []

        def process_search(prefix, pattern):
            found_keys = search_s3_objects(bucket_name, prefix, pattern)
            result = []
            for found_key in found_keys:
                object_url = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{found_key}"
                encode_dxf_filename = urllib.parse.quote(object_url, safe='/:')
                result.append(encode_dxf_filename)
            return result

        with ThreadPoolExecutor() as executor:
            future_to_search = {executor.submit(process_search, prefix, pattern): (prefix, pattern) for prefix, pattern in zip(s3_folder_name, wildcard_picture)}
            
            for future in as_completed(future_to_search):
                search_results = future.result()
                sub_dis_items.extend(search_results)
        print("写真のリスト追加にかかった時間_time4: ", time.time() - start4 )
        
# << ◆写真メモを作成するコード◆ >>
        start5 = time.time()
        bridge_damage = [] # すべての"bridge"辞書を格納するリスト

        bridge = {
            "parts_name": first_item[i],
            "damage_name": second_items[i] if i < len(second_items) else None  # second_itemsが足りない場合にNoneを使用
        }
        bridge_damage.append(bridge)

# << ◆1つ1つの部材に対して損傷を紐付けるコード◆ >>
        first_element = bridge_damage[0]

        # 'first'キーの値にアクセス
        first_value = first_element['parts_name']

        first_and_second = []
        #<<◆ 部材名が1種類かつ部材名の要素が1種類の場合 ◆>>
        if len(first_value) == 1: # 部材名称が1つの場合
            if len(first_value[0]) == 1: # 要素が1つの場合
                # カッコを1つ減らすためにリストをフラットにする
                flattened_first = [first_buzai_item for first_buzai_sublist in first_value for first_buzai_item in first_buzai_sublist]
                first_element['parts_name'] = flattened_first
                # 同様に 'second' の値もフラットにする
                second_value = first_element['damage_name']
                flattened_second = [second_name_item for second_name_sublist in second_value for second_name_item in second_name_sublist]
                first_element['damage_name'] = flattened_second

                first_and_second.append(first_element)
                #print(first_and_second) # [{'first': ['排水管 Dp0102'], 'second': ['①腐食(小大)-c', '⑤防食機能の劣化(分類1)-e']}]

            #<<◆ 部材名が1種類かつ部材名の要素が複数の場合 ◆>>
            else: # 別の部材に同じ損傷が紐付く場合
                    # 元のリストから各要素を取得
                for first_buzai_item in bridge_damage:
                    #print(item)
                    before_first_elements = first_buzai_item['parts_name'][0]  # ['床版 Ds0201', '床版 Ds0203']
                    first_elements = []

                    for first_buzai_second_name in before_first_elements:
                        if "～" in first_buzai_second_name:

                            first_step = first_buzai_second_name

                            if " " in first_step:
                                # 部材記号の前にスペースが「含まれている」場合
                                first_step_split = first_step.split()

                            else:
                                # 部材記号の前にスペースが「含まれていない」場合
                                first_step_split = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', first_step) # アルファベット以外とアルファベットの並びで分割
                                first_step_split = [kara for kara in first_step_split if kara] # re.split()の結果には空文字が含まれるので、それを取り除く

                            # 正規表現
                            number = first_step_split[1]
                            # マッチオブジェクトを取得
                            number_part = re.search(r'[A-Za-z]*(\d+～\d+)', number).group(1)

                            one = number_part.find("～")

                            start_number = number_part[:one]
                            end_number = number_part[one+1:]

                            # 最初の2桁と最後の2桁を取得
                            start_prefix = start_number[:2]
                            start_suffix = start_number[2:]
                            end_prefix = end_number[:2]
                            end_suffix = end_number[2:]

                            # 「主桁 Mg」を抽出
                            prefix_text = first_step_split[0] + " " + re.match(r'[A-Za-z]+', number).group(0)

                            # 決められた範囲内の番号を一つずつ追加
                            for prefix in range(int(start_prefix), int(end_prefix)+1):
                                for suffix in range(int(start_suffix), int(end_suffix)+1):
                                    number_items = "{}{:02d}{:02d}".format(prefix_text, prefix, suffix)
                                    first_elements.append(number_items)
                        else:
                            first_elements.append(first_buzai_second_name)
                    
                    
                    second_elements = first_buzai_item['damage_name'][0]  # ['⑦剥離・鉄筋露出-d']

                    
                    # first の要素と second を一対一で紐付け
                    for first_buzai_second_name in first_elements:
                        first_and_second.append({'parts_name': [first_buzai_second_name], 'damage_name': second_elements})

            #print(first_and_second) # [{'first': '床版 Ds0201', 'second': '⑦剥離・鉄筋露出-d'}, {'first': '床版 Ds0203', 'second': '⑦剥離・鉄筋露出-d'}]

        #<<◆ 部材名が複数の場合 ◆>>
        else:
            for double_item in bridge_damage:
                first_double_elements = double_item['parts_name'] # [['支承本体 Bh0101'], ['沓座モルタル Bm0101']]
                second_double_elements = double_item['damage_name'] # [['①腐食(小小)-b', '⑤防食機能の劣化(分類1)-e'], ['⑦剥離・鉄筋露出-c']]
                
                for break_first, break_second in zip(first_double_elements, second_double_elements):
                    first_and_second.append({'parts_name': break_first, 'damage_name': break_second})

        for damage_parts in bridge_damage:
            # print(damage_parts)
            if isinstance(damage_parts["damage_name"], list):  # "second"がリストの場合
                filtered_second_items = []
                for sublist in damage_parts["damage_name"]:
                    if isinstance(sublist, list):  # サブリストがリストである場合
                        if any(item.startswith('①') for item in sublist) and any(item.startswith('⑤') for item in sublist):
                            # ⑤で始まる要素を取り除く
                            filtered_sublist = [item for item in sublist if not item.startswith('⑤')]
                            filtered_second_items.append(filtered_sublist)
                        else:
                            filtered_second_items.append(sublist)
                    else:
                        filtered_second_items.append([sublist])
                
                # フィルタリング後のsecond_itemsに対して置換を行う                
                #pavement_items = {"first": first_item[i], "second": filtered_second_items}
                    
        combined_list = []
        if damage_parts["damage_name"] is not None:
            combined_second = filtered_second_items #if i < len(updated_second_items) else None
        else:
            combined_second = None
        
        combined = {"parts_name": first_item[i], "damage_name": combined_second}
        combined_list.append(combined)
        request_list = combined_list[0]
        # <<◆ secondの多重リストを統一させる ◆>>
        try:
            # データを取得する
            check_request_list = request_list['parts_name'][1]

            # 条件分岐
            if isinstance(check_request_list, list):
                request_list
                #print(request_list)
                
        except (KeyError, IndexError) as e:
            # KeyError や IndexError の例外が発生した場合の処理

            # secondの多重リストをフラットなリストに変換
            flat_list = [item for sublist in request_list['damage_name'] for item in sublist]
            # フラットなリストを再びサブリストに変換して格納
            request_list['damage_name'] = [flat_list]
            # 完成目標の確認
            
            test = request_list['damage_name'][0]

        # 先頭が文字（日本語やアルファベットなど）の場合
        def all_match_condition(lst):
            """
            リスト内のすべての項目が特定条件に一致するか確認します。
            ただし、空のリストの場合、Falseを返します。
            """
            # 空のリストの場合は False を返す
            if not lst:
                return False
            
            pattern = re.compile(r'\A[^\W\d_]', re.UNICODE)
            return all(pattern.match(item) for item in lst)

        if all_match_condition(test):
            request_list
        else:
            request_list['damage_name'] = [request_list['damage_name']]

        #<< ◆損傷メモの作成◆ >>
        replacement_patterns = {
            "①腐食(小小)-b": "腐食", # 1
            "①腐食(小大)-c": "全体的な腐食",
            "①腐食(大小)-d": "板厚減少を伴う腐食",
            "①腐食(大大)-e": "全体的に板厚減少を伴う腐食",
            "②亀裂-c": "塗膜割れ", # 2
            "②亀裂-e": "長さのある塗膜割れ・幅0.0mmの亀裂",
            "③ゆるみ・脱落-c": "ボルト・ナットにゆるみ、脱落(●本中●本)", # 3
            "③ゆるみ・脱落-e": "ボルト・ナットにゆるみ、脱落(●本中●本)",
            "④破断-e": "鋼材の破断", # 4
            "⑤防食機能の劣化(分類1)-e": "点錆", # 5
            "⑥ひびわれ(小小)-b": "最大幅0.0mmのひびわれ", # 6
            "⑥ひびわれ(小大)-c": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
            "⑥ひびわれ(中小)-c": "最大幅0.0mmのひびわれ",
            "⑥ひびわれ(中大)-d": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
            "⑥ひびわれ(大小)-d": "最大幅0.0mmのひびわれ",
            "⑥ひびわれ(大大)-e": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
            "⑦剥離・鉄筋露出-c": "コンクリートの剥離", # 7
            "⑦剥離・鉄筋露出-d": "鉄筋露出",
            "⑦剥離・鉄筋露出-e": "断面減少を伴う鉄筋露出",
            "⑧漏水・遊離石灰-c": "漏水", # 8
            "⑧漏水・遊離石灰-d": "遊離石灰",
            "⑧漏水・遊離石灰-e": "著しい遊離石灰・泥や錆汁の混入を伴う漏水",
            "⑨抜け落ち-e": "コンクリート塊の抜け落ち", # 9
            "⑪床版ひびわれ-b": "最大幅0.0mmの1方向ひびわれ", # 11
            "⑪床版ひびわれ-c": "最大幅0.0mmの1方向ひびわれ",
            "⑪床版ひびわれ-d": "最大幅0.0mmの1方向ひびわれ",
            "⑪床版ひびわれ-e": "最大幅0.0mmの角落ちを伴う1方向ひびわれ",
            "⑫うき-e": "コンクリートのうき", # 12
            "⑮舗装の異常-c": "最大幅0.0mmのひびわれ", # 15
            "⑮舗装の異常-e": "最大幅0.0mmのひびわれ・舗装の土砂化",
            "⑯定着部の異常-c": "定着部の損傷", # 16
            "⑯定着部の異常(分類2)-e": "定着部の著しい損傷",
            "⑳漏水・滞水-e": "漏水・滞水", # 20
            "㉓変形・欠損-c": "変形・欠損", # 23
            "㉓変形・欠損-e": "著しい変形・欠損",
            "㉔土砂詰まり-e": "土砂詰まり", # 24
        }

        def describe_damage(unified_request_list):
            described_list = []
            
            for damage in unified_request_list:
                if damage in replacement_patterns: # 辞書に一致する場合は登録文字を表示
                    described_list.append(replacement_patterns[damage])
                elif damage.startswith('⑰'): # 17の場合はカッコの中を表示
                    match = re.search(r'(?<=:)(.*?)(?=\)-e)', damage)
                    if match:
                        described_list.append(match.group(1))
                else:
                    pattern = r'[\u3248-\u3257](.*?)-'
                    match = re.search(pattern, damage)
                    if match:
                        described_list.append(match.group(1))
                    else:
                        described_list.append(damage)  # フォールバックとしてそのまま返す
            return ','.join(described_list)

        # 各ケースに対して出力を確認:
        def generate_report(unified_request_list):
            primary_damages = []
            processed_related_damages = []
            #print(f"unified_request_list：{unified_request_list}")
            first_items = unified_request_list['parts_name']
            #print(first_items) # [['支承本体 Bh0101'], ['沓座モルタル Bm0101']]
            second_items = unified_request_list['damage_name']
            #print(second_items) # [['①腐食(小小)-b', '⑤防食機能の劣化(分類1)-e'], ['⑦剥離・鉄筋露出-c']]
            primary_damages_dict = {}

            for first_item, second_item in zip(first_items, second_items):
                element_names = [f.split()[0] for f in first_item] # カッコ内の要素について、スペースより前を抽出
                #print(f"element_names：{element_names}") # ['支承本体'], ['沓座モルタル']
                damage_descriptions = describe_damage(second_item) # 辞書で置換
                #print(f"damage_descriptions：{damage_descriptions}") # 腐食,点錆, 剥離
                
                if len(element_names) == 1: # ['主桁', '横桁', '対傾構']：これはだめ
                    primary_damages.append(f"{element_names[0]}に{damage_descriptions}が見られる。")
                    #print(f"primary_damages：{primary_damages}") # ['支承本体に腐食,点錆が見られる。', '沓座モルタルに剥離が見られる。']
                else:
                    element_names = list(dict.fromkeys(element_names))            
                    joined_elements = "および".join(element_names[:-1]) + "," + element_names[-1]
                    if joined_elements.startswith(","):
                        new_joined_elements = joined_elements[1:]
                    else:
                        new_joined_elements = joined_elements
                    primary_damages.append(f"{new_joined_elements}に{damage_descriptions}が見られる。")

                for elem in first_item:
                    primary_damages_dict[elem] = second_item[:]

            primary_description = "また".join(primary_damages)
                
            for elem_name, elem_number in zip(first_items, second_items): # 主桁 Mg0101
                # リストをフラットにする関数
                def flatten_list(nested_list):
                    return [item for sublist in nested_list for item in sublist]
                
                # 辞書から 'first' と 'second' の値を取り出す
                first_list = request_list['parts_name']
                second_list = request_list['damage_name']

                # 'first' の要素数を数える
                first_count = sum(len(sublist) for sublist in first_list)

                # 'second' の要素数を数える
                second_count = sum(len(sublist) for sublist in second_list)
                # フラットにしたリストを比較
                if flatten_list(first_items) != elem_name and flatten_list(second_items) != elem_number:
                    sub_related_damages = []
                    for first_item in first_items:
                        for elem in first_item:
                            if elem in primary_damages_dict:
                                sub_related_damages.append(f"{elem}:{format_damages(primary_damages_dict[elem])}")

                    second_related_damages = [process_damage(damage, i) for i, damage in enumerate(sub_related_damages)]
                    processed_related_damages = process_related_damages(second_related_damages)

                elif first_count < 2 and second_count < 2:
                    pass

                else:
                    if first_count > 1 and second_count < 2:
                        first_items_from_first = first_item[1:]
                        related_damage_list = ','.join(first_items_from_first)
                        related_second_item = ','.join(second_item)
                    elif first_count < 2 and second_count > 1:
                        second_items_from_second = second_item[1:]
                        related_damage_list = ','.join(second_items_from_second)
                        processed_related_damages = [f"{','.join(elem_name)}:{related_damage_list}"]
                    else:
                        related_damage_list = ','.join(second_item)
                        processed_related_damages = [f"{','.join(elem_name)}:{related_damage_list}"]


            related_description = ""
            if processed_related_damages:
                related_description = "\n【関連損傷】\n" + ", ".join(processed_related_damages)

            return f"{primary_description} {related_description}".strip()

        combined_data = generate_report(request_list)
        # print(combined_data)
        # print(f"picture_urls：{picture_urls}")
        
                # \n文字列のときの改行文字
        items = {'parts_name': first_item[i], 'damage_name': second_items[i], 'join': first_and_second, 
                 'picture_number': third, 'this_time_picture': sub_dis_items, 'last_time_picture': None, 'textarea_content': combined_data, 
                 'damage_coordinate': damage_coordinate[i], 'picture_coordinate': picture_coordinate[i]}
        damage_table.append(items)
        print("damage_tableの作成にかかった時間_time5: ", time.time() - start5 )
    #優先順位の指定
    order_dict = {"主桁": 1, "横桁": 2, "床版": 3, "PC定着部": 4, "橋台[胸壁]": 5, "橋台[竪壁]": 6, "支承本体": 7, "沓座モルタル": 8, "防護柵": 9, "地覆": 10, "伸縮装置": 11, "舗装": 12, "排水ます": 13, "排水管": 14}
    order_number = {"None": 0, "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5, "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10, "⑪": 11, "⑫": 12, "⑬": 13, "⑭": 14, "⑮": 15, "⑯": 16, "⑰": 17, "⑱": 18, "⑲": 19, "⑳": 20, "㉑": 21, "㉒": 22, "㉓": 23, "㉔": 24, "㉕": 25, "㉖": 26}
    order_lank = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
            
    # <<◆ リストの並び替え ◆>>
    def sort_key_function(sort_item):
        first_value = sort_item['parts_name'][0][0] # firstキーの最初の要素
        #print(first_value) # 主桁 Mg0901

        if " " in first_value:
            # 部材記号の前にスペースが「含まれている」場合
            first_value_split = first_value.split()
            #print(first_value_split) # ['主桁', 'Mg0901']
        else:
            # 部材記号の前にスペースが「含まれていない」場合
            first_value_split = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', first_value) # アルファベット以外とアルファベットの並びで分割
            first_value_split = [x for x in first_value_split if x] # re.split()の結果には空文字が含まれるので、それを取り除く
            #print(f"first_value_split：{first_value_split}") # ['主桁', 'Mg0901']

        first_name_key = order_dict.get(first_value_split[0], float('inf'))
        #print(first_name_key) # 1
        if "～" in first_value_split[1]:
            match = re.search(r'[A-Za-z]+(\d{2,})(\D)', first_value_split[1])
            if match:
                first_number_key = int(match.group(1))
        else:
            first_number_key = int(first_value_split[1][2:])
        #print(first_number_key) # 901

        if sort_item['damage_name'][0][0]:  # `second`キーが存在する場合
            second_value = sort_item['damage_name'][0][0] # secondキーの最初の要素
            #print(second_value) # ⑰その他(分類6:異物混入)-e
            second_number_key = order_number.get(second_value[0], float('inf'))  # 先頭の文字を取得してorder_numberに照らし合わせる
            #print(second_number_key) # 17
            second_lank_key = order_lank.get(second_value[-1], float('inf'))  # 末尾の文字を取得してorder_lankに照らし合わせる
            #print(second_lank_key) # 5
        else:
            second_number_key = float('inf')
            second_lank_key = float('inf')
                
        return (first_name_key, first_number_key, second_number_key, second_lank_key)

    sorted_items = sorted(damage_table, key=sort_key_function)
    # print(f"sorted_items：{sorted_items}")
    return sorted_items
# ↑　インデックスを1つ左に移動した(return sorted_items以外)