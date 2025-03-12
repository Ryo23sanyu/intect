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
    extracted_text = find_square_around_text(table.article.id, table.infra.id, dxf_filename, search_title_text, second_search_title_text) # dxf_file.py
    # find_square_around_text関数の結果をextracted_text変数に格納
    print("関数スタート：find_square_around_text")
    # リストを処理して、スペースを追加する関数を定義
    def add_spaces(text):
        # 正規表現でアルファベットと数字の間にスペースを挿入
        return re.sub(r'(?<! )([a-zA-Z]+)(\d{2,})', r' \1\2', text)

    # 変更されたリストを保存するための新しいリスト
    new_extracted_text = []
    
    # print(f"処理前のリスト(tasks.py)　{extracted_text}")
    # 各サブリストを処理
    for sub_extracted_text in extracted_text:
        # リストに「''」が含まれていれば、その要素を削除
        if '' in sub_extracted_text:
            sub_extracted_text.remove('') #TODO
        # 先頭の文字列を修正
        if " " not in sub_extracted_text[0]:
            sub_extracted_text[0] = add_spaces(sub_extracted_text[0])
        # 新しいリストに追加
        new_extracted_text.append(sub_extracted_text)

    extracted_text = new_extracted_text
    
    print(f"CAD抽出データ(tasks.py)　{extracted_text}")

    damage_table = []
    picture_number = "" # 写真番号を保存するための変数
    
    for index, loop_extracted_text in enumerate(extracted_text):
        # break # CAD抽出データの確認用 
        # 〇 < リストの座標値を操作 > 〇
        list_count = sum(isinstance(list_item, list) for list_item in loop_extracted_text) # リストの中にリストがいくつあるか数える

        damage_coordinate  = ""
        picture_coordinate = ""

        if list_count == 2:
            choiced_picture = loop_extracted_text[-3] # 2つのリストが存在する場合 のみ 、写真指定が存在する
            damage_coordinate = loop_extracted_text[-2] # 座標削除前に逃がす
            picture_coordinate = loop_extracted_text[-1] # 座標削除前に逃がす
            del loop_extracted_text[-2:] # リストが2つある時、末尾2つの要素を削除
        elif list_count == 1:
            choiced_picture = None
            damage_coordinate = loop_extracted_text[-1] # 座標削除前に逃がす
            picture_coordinate = None
            del loop_extracted_text[-1:] # リストが1つある時、末尾1つの要素を削除
        else:
            choiced_picture = None
            damage_coordinate = None
            picture_coordinate = None


        # 〇 < リストの損傷種類と部材種類を操作 > 〇

        # 正規表現の設定
        name_and_4_number = r".*?(\s).*?([a-zA-Z]+).*?(\d+)" # 任意の文字(.*?) + スペース(\s) + アルファベット([a-zA-Z])1文字以上(+) + 任意の文字 + 数字(\d)1文字以上
        damage_26_pattern = r'[\u2460-\u2473\u3251-\u3256].*-[a-zA-Z]' # 丸数字とワイルドカードとアルファベット( ⓵腐食-d )

        # 部材種類もしくは損傷種類に一致した場合に抽出
        match_parts_or_damage = [mpod for mpod in loop_extracted_text if re.match(damage_26_pattern, mpod) or (re.match(name_and_4_number, mpod) and ('月' not in mpod or '日' not in mpod))]
        # print(f"match_parts_or_damage　{match_parts_or_damage}") # ['支承本体 Bh0201', '⑬遊間の異常-c', '㉔土砂詰まり-e', '沓座モルタル Bm0201', '⑫うき-e', '㉓変形・欠損-c', '落橋防止システム Sf0201', '⑦剥離・鉄筋露出-d']

        # 要素1つ1つを対象とする
        for index, single_parts_or_damage in enumerate(match_parts_or_damage):
            if "," in single_parts_or_damage: # 要素にコンマが含まれている場合、コンマで分割
                split = single_parts_or_damage.split(",") # ['主桁 Mg0308', '0309', '対傾構 Cf0209']
                
                joined_replace_list = []
                one_time_save = ""
                
                for item in split: # 分割した要素1つ1つを対象とする
                    # print(item[0])
                    if item[0].isdigit(): # 先頭が数字の場合(分割してはいけなかった場合)
                        
                        if len(one_time_save) > 0: # 既にone_time_saveに格納されている値とコンマで繋げる
                            one_time_save = one_time_save + "," + item
                            
                    else: # 先頭が数字以外の場合                
                        if len(one_time_save) > 0: # 前のループでone_time_saveに値が格納されている場合、リストに格納
                            joined_replace_list.append(one_time_save)
                            one_time_save = "" # 格納後、one_time_saveの値をリセット
                            
                        one_time_save = item # 先頭が数字以外の場合、one_time_saveに値を格納
                joined_replace_list.append(one_time_save) # 
                
                # print("list")
                # print(joined_replace_list)
                
                # print(len(joined_replace_list))
                
                match_parts_or_damage.remove(single_parts_or_damage)
                for insert in range(len(joined_replace_list)):
                    # print(joined_replace_list[insert])
                    match_parts_or_damage.insert(index+insert, joined_replace_list[insert])
        # print(match_parts_or_damage)
        
        
        # 数字を含む文字列を抽出
        match_parts_name = [na4n for na4n in match_parts_or_damage if (re.match(name_and_4_number, na4n) and ('月' not in na4n or '日' not in na4n))]
        # print(f"match_parts_name　{match_parts_name}") # ['支承本体 Bh0201', '沓座モルタル Bm0201']
        
        
        # 旗挙げの条件分岐
        if len(match_parts_name) > 1: # リストに含まれる部材名称が2つ以上の場合
            print(f"match_parts_name　{match_parts_name}")
            # print("2つ以上")
            parts_name_box = [] # 部材種類を格納する大外のリスト
            damage_pattern_box = [] # 損傷種類を格納する大外のリスト 
            
            first_parts_name_box = [] # 部材種類を格納する最初のリスト
            first_damage_pattern_box = [] # 損傷種類を格納する最初のリスト
            
            sub_parts_name_box = ""
            sub_damage_pattern_box = damage_pattern_box
            parts_name_counter = 1 # 何個目のリストかカウント
            damage_name_counter = 1 # 何個目のリストかカウント

            for loop in match_parts_or_damage: # enumerateを使用してforループをカウント( indexでカウント、loopはループの要素 )
                
                if (re.match(name_and_4_number, loop) and ('月' not in loop or '日' not in loop)): # loopの要素が　部材種類　の場合
                    
                    if len(first_damage_pattern_box) == 0: # 最初の損傷リストに値が格納されていない場合
                        first_parts_name_box.append(loop) # 最初の損傷リストに格納
                    
                    elif parts_name_counter == damage_name_counter + 1: # 部材リストは新しく作成されたが、損傷リストは空の場合
                        sub_parts_name_box.append(loop)
                    
                    else:
                        if parts_name_counter == 1: # 部材リストを新規作成した場合、最初の損傷リストを大外のリストに格納
                            parts_name_box.append(first_parts_name_box)

                        # 新しいリストを作成
                        sub_parts_name_box = f"parts_name_box_{parts_name_counter}" # sub_parts_name_box変数 の値を上書き
                        sub_parts_name_box = []
                        sub_parts_name_box.append(loop)
                        parts_name_box.append(sub_parts_name_box)
                        parts_name_counter += 1 # リストを新規作成したため、カウンターを更新
                    print(f"parts_name_box　{parts_name_box}")        
                        
                else: # loopの要素が　損傷種類　の場合
                    if parts_name_counter == 1:
                        first_damage_pattern_box.append(loop)

                    elif parts_name_counter == damage_name_counter:
                        sub_damage_pattern_box.append(loop)
                        
                    else:
                        if parts_name_counter != damage_name_counter and damage_name_counter == 1:
                            damage_pattern_box.append(first_damage_pattern_box)
                        
                        sub_damage_pattern_box = f"damage_pattern_box_{damage_name_counter}"
                        sub_damage_pattern_box = []
                        sub_damage_pattern_box.append(loop)
                        damage_pattern_box.append(sub_damage_pattern_box)
                        damage_name_counter += 1

            if len(parts_name_box) == 0: # 部材は複数だが損傷が同一の場合、forループが終了した段階で大外のリストに格納
                parts_name_box.append(first_parts_name_box)
                
            if len(damage_pattern_box) == 0:
                damage_pattern_box.append(first_damage_pattern_box)

            short_cut_parts_name = parts_name_box
            short_cut_damage_name = damage_pattern_box        

        else: # リストに含まれる部材名称が1つの場合
            # print("1つ")
            short_cut_parts_name = [match_parts_name]
            short_cut_damage_name = [[d26p for d26p in loop_extracted_text if re.match(damage_26_pattern, d26p)]] # リストから 損傷種類 を抽出(多重リストの場合はエラー)

        # 〇 < 旗挙げの省略記号（～）を分解してそれぞれに当てはめ > 〇
        create_elements = []
        parts_name = []
        
        print(f"ショートカット：{short_cut_parts_name}")
        print(len)

        for single_list_in_many_elements in short_cut_parts_name: # 1つ内側のリストでforループを実行し、各要素に対して実行
            print(f"single_list_in_many_elements　{single_list_in_many_elements}")
            list_in_split_elements = ",".join(single_list_in_many_elements).split(",")

            for unknown_initial_and_exist_number in list_in_split_elements: # コンマで分割した要素それぞれにforループを実行
                # print(unknown_initial_and_exist_number)
                if " " in unknown_initial_and_exist_number: # 要素に空白が含まれている場合(部材名称を含んでいる場合)
                    split_name_and_initial = unknown_initial_and_exist_number.split()
                    split_parts_name = split_name_and_initial[0] # 部材名称を取得
                    split_parts_initial = re.sub(r"[^a-zA-Z]", "", split_name_and_initial[1]) # 部材記号を取得
                else:
                    # 部材記号の前にスペースが「含まれていない」場合
                    split_name_and_initial = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', unknown_initial_and_exist_number) # アルファベット以外とアルファベットの並びで分割
                    split_name_and_initial = [short_cut_wave for short_cut_wave in split_name_and_initial if short_cut_wave] # re.split()の結果には空文字が含まれるので、それを取り除く
                    # split_name_and_initial.insert(0, split_parts_name)
                    
                # print(split_name_and_initial)
                
                if "～" in unknown_initial_and_exist_number:
                    # print(f"split_parts_name {split_parts_name}")

                    if len(split_name_and_initial) > 1:
                        parts_number = split_name_and_initial[1].replace(split_parts_initial, "")
                    else:
                        parts_number = split_name_and_initial[0]
                    
                    # マッチオブジェクトを取得
                    number_part = re.search(r'[A-Za-z]*(\d+～\d+)', parts_number).group(1)

                    index_wave = number_part.find("～")

                    start_number = number_part[:index_wave]
                    end_number = number_part[index_wave+1:]

                    # 最初の2桁と最後の2桁を取得
                    start_prefix = start_number[:2]
                    start_suffix = start_number[2:]
                    end_prefix = end_number[:2]
                    end_suffix = end_number[2:]

                    # 「主桁 Mg」を抽出
                    parts_name_and_initial = split_parts_name + " " + split_parts_initial

                    # 決められた範囲内の番号を一つずつ追加
                    for create_start_number in range(int(start_prefix), int(end_prefix)+1):
                        for create_end_number in range(int(start_suffix), int(end_suffix)+1):
                            create_four_number = "{}{:02d}{:02d}".format(parts_name_and_initial, create_start_number, create_end_number)
                            create_elements.append(create_four_number)
                elif unknown_initial_and_exist_number.isdigit():
                    parts_name_and_initial = split_parts_name + " " + split_parts_initial
                    create_elements.append(parts_name_and_initial + unknown_initial_and_exist_number)
                    
                else:
                    create_elements.append(unknown_initial_and_exist_number)
        
        if len(match_parts_name) > 1: # 多重リストの場合
            parts_name = parts_name_box
        else:
            parts_name.append(create_elements)
            
        damage_name = short_cut_damage_name

        # 〇 < リストの部材種類と損傷種類の組み合わせを操作 > 〇
        parts_name_join_damage_name = []
        for loop_index, first_buzai_second_name in enumerate(create_elements):            
            parts_name_join_damage_name.append({'parts_name': [first_buzai_second_name], 'damage_name': damage_name[loop_index] if len(damage_name) > 1 else damage_name[0]})
        # print(f"parts_name_join_damage_name {parts_name_join_damage_name}")


        # 〇 < リストの写真メモを操作 > 〇
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
            "⑤防食機能の劣化(分類1)-c": "塗膜のうき", # 5
            "⑤防食機能の劣化(分類1)-d": "塗膜の剥離",
            "⑤防食機能の劣化(分類1)-e": "点錆",
            "⑤防食機能の劣化(分類2)-c": "点錆",
            "⑤防食機能の劣化(分類2)-e": "点錆",
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
            "⑩補修・補強材の損傷(分類1)-c": "補修・補強材(鋼板)の損傷", # 10
            "⑩補修・補強材の損傷(分類1)-e": "補修・補強材(鋼板)の損傷",
            "⑩補修・補強材の損傷(分類2)-c": "補修・補強材(繊維)の損傷",
            "⑩補修・補強材の損傷(分類2)-e": "補修・補強材(繊維)の損傷",
            "⑩補修・補強材の損傷(分類3)-c": "補修・補強材(コンクリート)の損傷",
            "⑩補修・補強材の損傷(分類3)-e": "補修・補強材(コンクリート)の損傷",
            "⑩補修・補強材の損傷(分類4)-c": "補修・補強材(塗装)の損傷",
            "⑩補修・補強材の損傷(分類4)-e": "補修・補強材(塗装)の損傷",
            "⑩補修・補強材の損傷(分類5)-c": "補修・補強材(鋼板)の損傷",
            "⑩補修・補強材の損傷(分類5)-e": "補修・補強材(鋼板)の損傷",
            "⑪床版ひびわれ-b": "最大幅0.0mmの1方向ひびわれ", # 11
            "⑪床版ひびわれ-c": "最大幅0.0mmの1方向ひびわれ",
            "⑪床版ひびわれ-d": "最大幅0.0mmの1方向ひびわれ",
            "⑪床版ひびわれ-e": "最大幅0.0mmの角落ちを伴う1方向ひびわれ",
            "⑫うき-e": "コンクリートのうき", # 12
            "⑬遊間の異常-c": "遊間の狭まり", # 13
            "⑬遊間の異常-e": "遊間の接触",
            "⑭路面の凹凸-c": "段差量0.0mmの凹凸", # 14
            "⑭路面の凹凸-e": "段差量0.0mmの凹凸",
            "⑮舗装の異常-c": "最大幅0.0mmのひびわれ", # 15
            "⑮舗装の異常-e": "最大幅0.0mmのひびわれ・舗装の土砂化",
            "⑯定着部の異常-c": "定着部の損傷", # 16
            "⑯定着部の異常-e": "定着部の著しい損傷",
            "⑱支承部の機能障害(分類1)-e": "●●による機能障害", # 18
            "⑱支承部の機能障害(分類2)-e": "●●による機能障害",
            "⑲変色・劣化-e": "劣化", # 19
            "⑳漏水・滞水-e": "漏水・滞水", # 20
            "㉑異常な音・振動": "異常な音や振動", # 21
            "㉒異常なたわみ": "異常なたわみ", # 22
            "㉓変形・欠損-c": "変形・欠損", # 23
            "㉓変形・欠損-e": "著しい変形・欠損",
            "㉔土砂詰まり-e": "土砂詰まり", # 24
            "㉕沈下・移動・傾斜-e": "下部工や支承部の沈下・移動・傾斜", # 25
            "㉖洗掘-c": "深さ●●mmの洗掘", # 26
            "㉖洗掘-e": "深さ●●mmの著しい洗掘",
        }

        # replacement_patterns辞書に当てはめて変換
        def describe_damage(unified_request_list):
            damage_name_append_list = []
            
            for damage_name in unified_request_list: # リスト形式から辞書の左辺と同一の形に変換
            
                if damage_name in replacement_patterns: # 辞書に一致する場合、登録文字を抽出して damage_name_append_list リストに格納
                    damage_name_append_list.append(replacement_patterns[damage_name])
                    
                elif damage_name.startswith('⑰'): # 17の場合はカッコの中を表示
                    match = re.search(r'(?<=:)(.*?)(?=\)-e)', damage_name) # コロン(：)と「)-e」の間の文字を抽出して damage_name_append_list リストに格納
                    if match:
                        damage_name_append_list.append(match.group(1))
                else:
                    match = re.search(r'[\u3248-\u3257](.*?)-', damage_name) # 登録していない場合は、損傷名のみを抽出して damage_name_append_list リストに格納
                    if match:
                        damage_name_append_list.append(match.group(1))
                    else:
                        damage_name_append_list.append(damage_name) # 正規表現に一致しない場合はそのまま( 丸番号～判定 ) damage_name_append_list リストに格納

            return ','.join(damage_name_append_list) # 取得した damage_name_append_list リストの要素をコンマ( , )で繋げて返す

        shape_up_picture_comments = []
        primary_damages_dict = {}

        for loop_parts_name, loop_damage_name in zip(short_cut_parts_name, short_cut_damage_name):
        
            split_parts_name = [single_parts_name_and_number.split()[0] for single_parts_name_and_number in loop_parts_name] # リストの要素をforループで分解し、各要素のスペースから前を抽出
            appended_damage_name = describe_damage(loop_damage_name) # 辞書で置換した結果
            
            print(split_parts_name)
            print(appended_damage_name)
            
            if len(split_parts_name) == 1: # リストの部材が1種類の場合( ['主桁', '横桁', '対傾構']：これはだめ )
                shape_up_picture_comments.append(f"{split_parts_name[0]}に{appended_damage_name}が見られる。")
                # print(f"shape_up_picture_comments：{shape_up_picture_comments}") # ['支承本体に腐食,点錆が見られる。', '沓座モルタルに剥離が見られる。']
                
            else: # リストの部材が2種類以上の場合( ['主桁', '横桁']：このような場合 )
                list_parts_name = list(dict.fromkeys(split_parts_name))
                joined_elements = "および".join(list_parts_name[:-1]) + "," + list_parts_name[-1] # 要素の1つ目と2つ目は「および」で結合、3つ目以降はコンマで結合
                if joined_elements.startswith(","): # 先頭にコンマが来た場合、2文字目から
                    joined_text_elements = joined_elements[1:]
                else:
                    joined_text_elements = joined_elements
                shape_up_picture_comments.append(f"{joined_text_elements}に{appended_damage_name}が見られる。")

            for elem in loop_parts_name: # 各部材種類に対してforループを実行
                primary_damages_dict[elem] = loop_damage_name[:] # 各部材1つずつに対して、損傷種類を割り振り

        joined_picture_comments = "また".join(shape_up_picture_comments[:-1]) + shape_up_picture_comments[-1]

        if "見られる。" in joined_picture_comments:
            joined_picture_comments = joined_picture_comments.replace('見られる。', '見られ、', joined_picture_comments.count('見られる。')-1) # 置換の最大回数を指定(最後の1つは置換しない)


        # print("特記なき損傷")
        other_attach_damage_list = []
        other_shape_up_text = ""
        
        for other_parts_name, other_damage_name in zip(short_cut_parts_name, short_cut_damage_name):
            if len(other_parts_name) != 1 or len(other_damage_name) != 1:
                if len(other_parts_name) == 1:
                    join_other_text = ",".join(other_parts_name) + ":" + ",".join(other_damage_name)
                    other_attach_damage_list.append(join_other_text)
                else:
                    many_parts_name_list = []
                    for list_in_parts_name in range(len(other_parts_name)):
                        
                        many_join_other_texts = other_parts_name[list_in_parts_name] + ":" + ",".join(other_damage_name)
                        many_parts_name_list.append(many_join_other_texts)
                    join_many_parts_name_list = ",".join(many_parts_name_list)  
                    other_attach_damage_list.append(join_many_parts_name_list)
                other_shape_up_text = "\n【関連損傷】\n" + ",".join(other_attach_damage_list)
        
        textarea_content = joined_picture_comments + other_shape_up_text
        # print(f"textarea_content {textarea_content}")


        # 〇 < リストの写真番号(写真番号-00)を操作 > 〇
        # picture_number = ""
        for picture_number_00 in loop_extracted_text:
            if "写真" in picture_number_00:
                picture_number = picture_number_00
                break # 「写真」を見つけたらforループを終了
            else: # 1つも見つけられなければ False となる
                picture_number = None
        # print(picture_number)


        # 〇 < リストの写真指定番号(1月23日 S123)を操作 > 〇
        def remove_bracket_and_included(choices_picture): # カッコとその中身を削除する関数
            bracket = re.compile(r"\([^()]*\)")
            result = [bracket.sub("", in_bracket) for in_bracket in choices_picture]
            return result

        shape_up_choiced_picture = []
        
        if isinstance(choiced_picture, str) and ',' in choiced_picture: # 文字列かつカンマが入っている(写真の指定が複数)
            # print("カンマあり")
            search_comma = r',(?![^(]*\))'
            split_comma_choiced_picture = re.split(search_comma, choiced_picture) # カンマが含まれている場合カンマで分割
            other_delete_choiced_picture = remove_bracket_and_included(split_comma_choiced_picture) # カッコとその中身を削除
            
            month_and_day = ""
            for single_choiced_picture in other_delete_choiced_picture: # リストに格納した各写真番号に対し、forループを実行
                # print(single_choiced_picture)
                # イニシャルの補完(days_and_initialに格納されるのは後半のため、2周目以降で起動)
                if single_choiced_picture.isdigit() and len(days_and_initial) > 0: # forループの single_choiced_picture変数 が数字のみ(写真指定が省略)かつ days_and_initial に値が含まれている場合
                    single_choiced_picture = days_and_initial + single_choiced_picture # single_choiced_picture変数を上書き
                # 日付の補完
                target = ' ' # 半角スペース
                if target in single_choiced_picture: # 半角スペースが single_choiced_picture変数 に含まれている場合 = 日付指定がある場合
                    space_index = single_choiced_picture.find(target)
                    month_and_day = single_choiced_picture[:space_index] # 月日のデータを保存
                elif len(month_and_day) > 0: # Falseの場合(半角スペースが含まれていない場合)かつ month_and_day変数 に値が含まれている場合
                    single_choiced_picture = month_and_day + " " + single_choiced_picture # single_choiced_picture変数を上書き
                
                picture_initial = ",".join(re.findall('[a-zA-Z]+', single_choiced_picture)) # イニシャルを取得
                picture_insert_wildcard = single_choiced_picture.replace(picture_initial, picture_initial + "*/*") # イニシャルと数字の間に */* を挿入してワイルドカード検索を行えるようにする
                days_and_initial = single_choiced_picture[:(single_choiced_picture.index(picture_initial) + len(picture_initial))] # 写真番号までのインデックス番号を取得して day_and_initial変数 に格納
                # print(f"days_and_initial{days_and_initial}")
                shape_up_choiced_picture.append(picture_insert_wildcard)

        elif isinstance(choiced_picture, str) and ',' not in choiced_picture: # 文字列かつカンマを含まない(写真の指定が単一)
            # print("カンマなし")
            bracket = r'\(.*?\)'
            other_delete_choiced_picture = re.sub(bracket, '', choiced_picture)
            picture_initial = ",".join(re.findall('[a-zA-Z]+', other_delete_choiced_picture)) # イニシャルを取得

            if len(picture_initial) > 0: # イニシャルを取得した場合(写真番号が指定されている場合)
                picture_insert_wildcard = other_delete_choiced_picture.replace(picture_initial, picture_initial + "*/*") # イニシャルと数字の間に */* を挿入してワイルドカード検索を行えるようにする
                # print(picture_insert_wildcard)
                shape_up_choiced_picture.append(picture_insert_wildcard)
            else:
                shape_up_choiced_picture.append("None")
        else:
            # print("写真がない")
            shape_up_choiced_picture = None
            
        if shape_up_choiced_picture == None:
            shape_up_choiced_picture = []
        
        # 4桁未満の場合は数字の前に 0 を挿入して4桁の数字とする(71 → 0071)        
        format_four_number_picture = []
        for loop_single_picture in shape_up_choiced_picture:
            target = '*/*'
            wildcard_index = loop_single_picture.find(target)
            pure_number = loop_single_picture[wildcard_index+3:]
            day_and_initial_and_wildcard = loop_single_picture.replace(pure_number, "") # 7, 47 
            zero_in_four_number = "{:0>4}".format(pure_number) # 数字の先頭に 0 を追加し、4桁に調整( そのため、0001～9999までの写真指定しか対応不可 )
            format_four_number_picture.append(day_and_initial_and_wildcard + zero_in_four_number) # ['0007', '0047']
        
        
        # print(f"format_four_number_picture　{format_four_number_picture}")
        name_and_wildcard_number = [item + ".jpg" for item in format_four_number_picture]
        
        name_replace_and_wildcard_picture = [] # 写真のイニシャルを登録した名前に変換した要素を入れるリスト
        for single_picture_initial in name_and_wildcard_number:
            if isinstance(name_and_wildcard_number, list): #  第一引数(name_and_wildcard_number)の形式が第二引数(list)であるか判断
                sorted_replacements = get_sorted_replacements(table.article.id)
                name_item = reduce(lambda acc, pair: acc.replace(pair[0], pair[1]), sorted_replacements, single_picture_initial)
                name_replace_and_wildcard_picture.append(name_item)
        # print(f"name_replace_and_wildcard_picture　{name_replace_and_wildcard_picture}")
        # ['9月8日 佐藤*/*0117.jpg', '9月8日 佐藤*/*0253.jpg']
        
        
        # << S3にアップロードした写真のワイルドカード検索 >>
        this_time_picture = []
        picture_upload_check = "in_picture" # TODO：写真のアップロードを確認する
        
        if picture_upload_check == "in_picture": # TODO：in_pictureの場合、写真を格納
            print(f"旗挙げ写真の検索中...")
            s3 = boto3.client('s3')
            bucket_name = 'infraprotect'
            article_folder_name = table.article.案件名
            infra_folder_name = table.infra.title

            pattern = r'\(.*?\)|\.jpg|\*'  # カッコとその中・「.jpg」・「*」を削除
            split_wildcard_lists = [re.split(r'[,/]', re.sub(pattern, '', item)) for item in name_replace_and_wildcard_picture]
            s3_folder_name = [f"{article_folder_name}/{infra_folder_name}/{item[0]}/" for item in split_wildcard_lists if len(item) >= 1]
            wildcard_picture = tuple(item[1] for item in split_wildcard_lists if len(item) >= 2)  # ('0117', '0253')
            
            @lru_cache(maxsize=None)
            def search_s3_objects(bucket, prefix, pattern):
                paginate = s3.get_paginator("list_objects_v2")
                matching_keys = []
                # print(f"prefix{prefix}") # 案件名～撮影者までのフォルダ名(article/infra/1月23日　佐藤)
                # print(f"pattern　{pattern}") # 写真番号(例：92)
                
# {'Key': '長生土木13橋/さかもり上/11月1日\u3000小玉/Resized/PB010835.jpg', 'LastModified': datetime.datetime(2025, 1, 15, 5, 28, 27, tzinfo=tzutc()), 'ETag': '"cfb75113a91515ca67b69e4a73a2af8a"', 'ChecksumAlgorithm': ['CRC64NVME'], 'Size': 97140, 'StorageClass': 'STANDARD'}
                for page in paginate.paginate(Bucket=bucket, Prefix=prefix): # フォルダ名が一致するS3バケット内の全てを取得    
                    if 'Contents' in page: # S3バケット内にContents(写真)が含まれている場合
                        for obj in page['Contents']: # バケット内の写真を1つずつ当てはめ
                            key = obj['Key']
                            if fnmatch.fnmatch(key, f"{prefix}*{pattern}.jpg"): # 一致した場合、matching_keysリストに格納
                                matching_keys.append(key)
                return matching_keys
                
                # TODO　フォルダ名( article/infra/1月23日　佐藤 )の写真を全量チェックし、写真番号が一致( 92 )した場合、matching_keyに返却しているため、多量の時間が掛かっている
                # for page in paginate.paginate(Bucket=bucket, Prefix=prefix): # フォルダ名が一致するS3バケット内の全てを取得
                    
                #     if 'Contents' in page: # S3バケット内にContents(写真)が含まれている場合
                #         matching_keys = [obj['Key'] for obj in page['Contents'] if fnmatch.fnmatch(obj['Key'], f"{prefix}*{pattern}.jpg")] # 一致した場合、matching_keysリストに格納
                #         print(f"matching_keys　{matching_keys}")
                # return matching_keys
            
            
            def process_search(prefix, pattern):
                found_keys = search_s3_objects(bucket_name, prefix, pattern)
                # print(f"found_keys　{found_keys}")
                
                # TODO found_keyに舗装の写真が1種類しか入っていない(Pm0201 D341)
                result = []
                for found_key in found_keys:
                    object_url = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{found_key}"
                    print(f"found_key　{found_key}")
                    encode_dxf_filename = urllib.parse.quote(object_url, safe='/:')
                    result.append(encode_dxf_filename)
                return result

            with ThreadPoolExecutor() as executor:
                future_to_search = {executor.submit(process_search, prefix, pattern): (prefix, pattern) for prefix, pattern in zip(s3_folder_name, wildcard_picture)}
                
                for future in as_completed(future_to_search):
                    search_results = future.result()
                    this_time_picture.extend(search_results)

        # 写真が見つからない場合、空白となるが、空白だと写真の変更ができない。
        # そこで、this_time_pictureに値が含まれている場合、save_this_time_pictureに一時保存
        # 次にpicture_numberに文字(写真番号-00)がある、かつ、None以外、かつ、this_time_pictureが空白( [] )の時、保存したsave_this_time_pictureをthis_time_pictureに当てはめる
        
        if len(this_time_picture) > 0:
            save_this_time_picture = this_time_picture
                    
        if picture_number != None and len(this_time_picture) == 0:
            this_time_picture = save_this_time_picture

# TODO 写真が意図していない箇所に入っている
        # print(f"parts_name　{parts_name}")
        # print(f"damage_name　{damage_name}")
        # print(f"picture_number　{picture_number}")
        # print(f"this_time_picture　{this_time_picture}")
        # print("")
        # 〇 < 形式を整える > 〇
        items = {'parts_name': parts_name, # 済
                'damage_name': damage_name, # 済
                'join': parts_name_join_damage_name, # 済
                'picture_number': picture_number, # 済
                'this_time_picture': this_time_picture, # 
                'last_time_picture': None, # 済
                'textarea_content': textarea_content, # 済
                'damage_coordinate': damage_coordinate, # 済
                'picture_coordinate': picture_coordinate # 済
                }
        
        damage_table.append(items)

    #  〇 < 並び替え > 〇
    #優先順位の指定
    order_dict = {"主桁": 101, "横桁": 102, "縦桁": 103, "床版": 104, "対傾構": 105, "上横構": 106, "下横構": 107, "アーチリブ": 108, "補剛桁": 109, "吊り材": 110, 
                  "支柱": 111, "橋門構": 112, "外ケーブル": 113, "ゲルバー部": 114, "PC定着部": 115, "格点": 116, "コンクリート埋込部": 117, "その他": 118, 
                  "橋脚[柱部・壁部]": 201, "橋脚[梁部]": 202, "橋脚[隅角部・接合部]": 203, "橋台[胸壁]": 204, "橋台[竪壁]": 205, "橋台[翼壁]": 206, "基礎[フーチング]": 207, "基礎": 208, 
                  "支承本体": 301, "アンカーボルト": 302, "沓座モルタル": 303, "台座コンクリート": 304, "落橋防止システム": 305, 
                  "高欄": 401, "防護柵": 402, "地覆": 403, "中央分離帯": 404, "伸縮装置": 405, "遮音施設": 406, "照明施設": 407, "縁石": 408, "舗装": 409, "排水ます": 410, 
                  "排水管": 411, "点検施設": 412, "添架物": 413, "袖擁壁": 414}
    order_number = {"None": 0, "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5, "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10, "⑪": 11, "⑫": 12, "⑬": 13, "⑭": 14, "⑮": 15, "⑯": 16, "⑰": 17, "⑱": 18, "⑲": 19, "⑳": 20, "㉑": 21, "㉒": 22, "㉓": 23, "㉔": 24, "㉕": 25, "㉖": 26}
    order_lank = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        

    # <<◆ リストの並び替え ◆>>
    def sort_key_function(sort_item): # damage_tableに格納されているリストを並び替え
        if len(sort_item['parts_name']) > 0: # リストのparts_nameキーに値が含まれている場合
            search_parts_name = sort_item['parts_name'][0][0] # 文字列として抽出
            bracket = r'\(.*?\)'
            parts_name_and_number = re.sub(bracket, '', search_parts_name) # かっことその中身を空白で置換 = 削除(主桁 Mg0901)

        if " " in parts_name_and_number: # 部材記号の前にスペースが含まれている場合
            split_parts_name_and_number = parts_name_and_number.split()
        else: # 部材記号の前にスペースが含まれていない場合
            parts_name_and_number_split = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', parts_name_and_number) # アルファベット以外とアルファベットが隣り合っている箇所で分割( PC定着部Cn0101 → PC定着部 Cn0101 )
            split_parts_name_and_number = [x for x in parts_name_and_number_split if x] # re.split()の結果には空文字が含まれるので、それを取り除く
            print(f"split_parts_name_and_number：{split_parts_name_and_number}") # ['主桁', 'Mg0901']

        parts_name_key = order_dict.get(split_parts_name_and_number[0], float('inf')) # order_dictに対応した数字(部材の順番)を返す
        
        
        if "～" in split_parts_name_and_number[1]: # 分割した要素番号の中に「～」が含まれていた場合
            match = re.search(r'[A-Za-z]+(\d{2,})(\D)', split_parts_name_and_number[1])
            if match:
                parts_number_key = int(match.group(1)) # 2文字以上の数字を返す
        elif "," in split_parts_name_and_number[1]: # 分割した要素番号の中に「 , 」が含まれていた場合
            split_number = split_parts_name_and_number[1].split(",")
            parts_number_key = int(re.sub(r"\D", "", split_number[0])) # 数字以外を空白で置換して、有効数字を返す(Mg0101 → 101) 
        else:
            parts_number_key = int(re.sub(r"\D", "", split_parts_name_and_number[1]))


        if sort_item['damage_name'][0][0]: # リストのparts_nameキーの中、1つ目の損傷種類が含まれている場合
            first_damage_and_lank = sort_item['damage_name'][0][0] # secondキーの最初の要素
            damage_name_key = order_number.get(first_damage_and_lank[0], float('inf')) # 先頭の文字(1～26)を取得してorder_numberに対応した数字(損傷の順番)を返す
            damage_lank_key = order_lank.get(first_damage_and_lank[-1], float('inf')) # 末尾の文字(a～e)を取得してorder_lankに対応した数字(判定の順番)を返す
        else:
            damage_name_key = float('inf')
            damage_lank_key = float('inf')
            
        # Y座標の小さい順（左から順番）に並び替え
        if sort_item['damage_coordinate']: # リストのparts_nameキーの中、1つ目の損傷種類が含まれている場合
            damage_coordinate_x = sort_item['damage_coordinate'][0]
            damage_coordinate_y = sort_item['damage_coordinate'][1]

        return (parts_name_key, parts_number_key, damage_name_key, damage_lank_key, damage_coordinate_x, damage_coordinate_y) # sort_key_function関数に結果を返す

    sorted_items = sorted(damage_table, key=sort_key_function)
    # print(f"sorted_items(tasks.py)　{sorted_items}")
    return sorted_items # create_picturelist関数に並び替えたdamage_tableの値を返す