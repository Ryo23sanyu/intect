import os
from pathlib import Path
import re

import boto3
import ezdxf

from infra.models import Article, Infra

# << dxfファイルの座標から、MTextとdefpointsを紐付け >>
def entity_extension(mtext, neighbor):
    # MTextの挿入点
    mtext_insertion = mtext.dxf.insert
    # print(f"Mtextの挿入点(dxf_file.py)：{mtext_insertion}")
    # print(mtext.dxf)
    # 特定のプロパティ(Defpoints)で描かれた文字の挿入点
    neighbor_insertion = neighbor.dxf.insert
    # print(f"defpointsの挿入点(dxf_file.py)：{neighbor_insertion}")
    # テキストの行数を求める
    text = mtext.plain_text()
    text_lines = text.split("\n") if len(text) > 0 else []
    # 改行で区切ったリスト数→行数
    text_lines_count = len(text_lines)
    # print(f"行数:{text_lines_count}")
    # Defpointsを範囲内とするX座標範囲
    x_start = mtext_insertion[0] # X開始位置(X座標：水平方向)
    x_end   = mtext_insertion[0] + mtext.dxf.width # X終了位置= 開始位置＋幅
    y_start = mtext_insertion[1] + mtext.dxf.char_height # Y開始位置(Y座標：上下方向)
    y_end   = mtext_insertion[1] - mtext.dxf.char_height * (text_lines_count) # 文字の高さ×(行数) (1行分、下方向に余裕を見ている)
    
    if 2*(y_start - y_end) <= (x_end - x_start): # オブジェクト高さ(y座標)の2倍値よりオブジェクト幅(x座標)の方が大きい場合
        x_end = mtext_insertion[0] + (mtext.dxf.width * 1/2) # x_endの値を半分にする(横に伸びすぎていると別の defpoints を拾ってしまう)
    
    # MTextの下、もしくは右に特定のプロパティで描かれた文字が存在するかどうかを判定する(座標：右が大きく、上が大きい)
    if (neighbor_insertion[0] >= x_start and neighbor_insertion[0] <= x_end):
        #y_endの方が下部のため、y_end <= neighbor.y <= y_startとする
        if (neighbor_insertion[1] >= y_end and neighbor_insertion[1] <= y_start):
            #print("枠内")
            return True
    
    return False

# << 座標値からdefpoints枠内の文字列のみ取得 >>
def find_square_around_text(article_pk, pk, dxf_filename, search_title_text, second_search_title_text):
    print("find_square_around_text関数の実行")
    article = Article.objects.filter(id=article_pk).first()
    infra = Infra.objects.filter(id=pk).first()
    
    # << S3からdxfファイルのダウンロード >>
    bucket_name = 'infraprotect'
    object_key = f'{article.案件名}/{infra.title}/{infra.title}.dxf'
    
    # ファイルパスにファイル名を含める
    # local_file_path = f'{str(Path.home() / "Desktop")}\intect_dxf\{article.案件名}\{infra.title}\{infra.title}.dxf'
    local_file_path = os.path.join(str(Path.home() / "Desktop"), "intect_dxf", article.案件名, infra.title, f'{infra.title}.dxf')
    def download_dxf_from_s3(bucket_name, object_key, local_file_path):
        s3 = boto3.client('s3')

        try:
            # フォルダが存在しない場合は作成
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # S3からファイルを指定したパスにダウンロード
            s3.download_file(bucket_name, object_key, local_file_path)
            print("ファイルのダウンロードが完了しました。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

    # 関数を呼び出す TODO：遅い箇所
    download_dxf_from_s3(bucket_name, object_key, local_file_path)

    # ローカルファイルをezdxfで読み込む
    try:
        doc = ezdxf.readfile(local_file_path)
        msp = doc.modelspace()
    except IOError as e:
        print(f"ファイルの読み込みに失敗しました: {e}")
    except ezdxf.DXFStructureError as e:
        print(f"DXF構造エラー: {e}")
    
    text_positions = [] # 見つかったテキストの位置を格納するためのリストを作成
    extracted_text = []
    
    print("dxfファイル読み取り開始")
    # MTEXTエンティティの各要素をtextという変数に代入してループ処理
    for mtext_insert_point in msp.query('MTEXT'): # モデルスペース内の「MTEXT」エンティティをすべて照会し、ループ処理
        #print(f"insert_points：{mtext_insert_point.dxf.text}")
        if mtext_insert_point.dxf.text == search_title_text:# target_text: # エンティティのテキストが検索対象のテキストと一致した場合
            text_insertion_point = mtext_insert_point.dxf.insert # テキストの挿入点(dxf.insert)を取得します。
            #print(f"true_text_insertion_point：{text_insertion_point}")
            text_positions.append(text_insertion_point[0]) # 挿入点のX座標をリストに保存
            break
    if not text_positions: # text_positionsリストが空の場合(見つけられなかった場合)
        for mtext_insert_point in msp.query('MTEXT'): # モデルスペース内の「MTEXT」エンティティをすべて照会し、ループ処理
            if mtext_insert_point.dxf.text == second_search_title_text:# second_target_text: # エンティティのテキストが検索対象のテキストと一致した場合
                text_insertion_point = mtext_insert_point.dxf.insert # テキストの挿入点(dxf.insert)を取得します。
                #print(f"false_text_insertion_point：{text_insertion_point}")
                text_positions.append(text_insertion_point[0]) # 挿入点のX座標をリストに保存
                break
        
    # Defpointsレイヤーで描かれた正方形枠の各要素をsquare変数に代入してループ処理
    for defpoints_square in msp.query('LWPOLYLINE[layer=="Defpoints"]'): # 
        if len(defpoints_square) == 4: # 正方形(=4辺)の場合
            square_x_values = [four_points[0] for four_points in defpoints_square] # squareというリストをループして各点(point)からx座標(インデックス0の要素)を抽出
            square_min_x = min(square_x_values) # 枠の最小X座標を取得
            square_max_x = max(square_x_values) # 枠の最大X座標を取得
        print(f"MAX:{square_min_x}")
        print(f"MIN:{square_max_x}")
        print(f"ポジション:{text_positions}")
        # 文字のX座標が枠の最小X座標と最大X座標の間にあるかチェック
        # text_positionsの各要素をtext_x_positionという変数に代入してforループを処理
        for text_x_position in text_positions:
            # 文字の座標がDefpoints枠のX座標内にある場合
            if square_min_x <= text_x_position <= square_max_x:
                # print(list(square)) 4点の座標を求める 
                left_top_point = list(defpoints_square)[0][0] # 左上の座標
                right_top_point = list(defpoints_square)[1][0] # 右上の座標
                right_bottom_point = list(defpoints_square)[2][0] # 右下の座標
                left_bottom_point = list(defpoints_square)[3][0] # 左下の座標
                defpoints_max_x = max(left_top_point,right_top_point,left_bottom_point,right_bottom_point) # X座標の最大値
                defpoints_min_x = min(left_top_point,right_top_point,left_bottom_point,right_bottom_point) # X座標の最小値
                
                print(f"defpoints_max_x：{defpoints_max_x}")
                print(f"defpoints_min_x：{defpoints_min_x}")
                
    if len(text_positions) == 0:
        print("dxfファイルエラー")
        print("dxfファイル上のタイトル「径間番号」もしくは「損傷図」が見つかりませんでした。")
        print("マルチテキストで「1径間」もしくは「損傷図」の記載が必要です。")
        
    
    # 指定したX座標範囲内にあるテキストを探す
    for circle_in_text in msp.query('MTEXT'):
        # print(f"サークル内(dxf_file.py)：{circle_in_text.dxf.insert.x}")
        if defpoints_min_x <= circle_in_text.dxf.insert.x <= defpoints_max_x and circle_in_text.dxf.layer != 'Defpoints':
        # MTextのテキストを抽出する
            text = circle_in_text.plain_text()
            #print(text)
            x, y, _ = circle_in_text.dxf.insert
            #print(x, y, _)
            if not text.startswith("※"):
                #print("※から始まらない")
                cad_data = text.split("\n") if len(text) > 0 else [] # .split():\nの箇所で配列に分配
                # if len(cad_data) > 0 and not text.startswith("※") and not any(keyword in text for keyword in ["×", ".", "損傷図"]):
                if len(cad_data) > 0 and (any(keyword in text for keyword in ["支承本体"]) or not any(keyword in text for keyword in ["×", ".", "mm", "本", "/", "損傷図", "NON-a", "⑪-a", "⑪-b", "⑪-c", "⑪-d", "⑪-e"])) and not text.endswith("径間"):
                # 文字長さが1文字以上あり、keyword の中に指定した文字が含まれていない    
            # 改行を含むかどうかをチェックする(and "\n" in cad):# 特定の文字列で始まるかどうかをチェックする: # 特定の文字を含むかどうかをチェックする
                    #print("有効な文字列")
                    related_text = "" # 見つけたMTextと関連するDefpointsレイヤの文字列を代入する変数
            # MTextの下、もしくは右に特定のプロパティ(Defpoints)で描かれた文字を探す
                    for neighbor in msp.query('MTEXT[layer=="Defpoints"]'): # DefpointsレイヤーのMTextを抽出
                        #print(f"neighbor:{neighbor}")
                    # MTextの挿入位置と特定のプロパティで描かれた文字の位置を比較する
                        if entity_extension(circle_in_text, neighbor):
                            #print("存在している")
                        # 特定のプロパティ(Defpoints)で描かれた文字のテキストを抽出する
                            related_text = neighbor.plain_text()
                            print(f"DXFテキストデータ:{related_text}")
                            #print(f"DXFデータ：{neighbor.dxf}")
                            defx, defy, _ = neighbor.dxf.insert
                        #extracted_text.append(neighbor_text)
                            break # 文字列が見つかったらbreakによりforループを終了する

                    if len(related_text) > 0: #related_textに文字列がある＝Defpointsレイヤから見つかった場合
                       cad_data.append(related_text[:]) # cad_dataに「部材名～使用写真」までを追加
                       cad_data.append([str(x), str(y)]) # 続いてcad_dataに「MTEXT」のX,Y座標を追加
                       print(f"cadデータ：{cad_data}")
                #最後にまとめてcad_dataをextracted_textに追加する
                
                    #print(f"defpoints_x座標：{defx}")
                    #print(f"defpoints_y座標：{defy}")
                    extracted_text.append(cad_data[:] + [[str(defx), str(defy)]]) # extracted_textに「MTEXTとその座標」およびdefのX,Y座標を追加
                
# << ※特記なき損傷の抽出用 ↓ >>                            
            else:
                lines = text.split('\n')# 改行でテキストを分割してリスト化
                sub_text = [[line] for line in lines]# 各行をサブリストとして持つ多重リストを構築

                pattern = r"\s[\u2460-\u3256]"# 文字列のどこかにスペース丸数字の並びがあるかをチェックする正規表現パターン
                pattern_start = r"^[\u2460-\u3256]"  # 文字列の開始が①～㉖であることをチェックする正規表現パターン
                pattern_anywhere = r"[\u2460-\u3256]"  # 文字列のどこかに①～㉖があるかをチェックする正規表現パターン
                last_found_circle_number = None  # 最後に見つかった丸数字を保持する変数

                # リストを逆順でループし、条件に応じて処理
                for i in range(len(sub_text)-1, -1, -1):  # 後ろから前にループ
                    item = sub_text[i][0]  # textリストの各サブリストの最初の要素（[0]）をitem変数に代入（地覆 ㉓-c）
                    if item.startswith("※"):
                        sub_text.remove(sub_text[i]) # 配列から除外する
                    elif re.search(pattern, item):  # itemが正規表現patternと一致している場合（スペース丸数字の並びがある）
                        last_found = item  # last_found変数にitem要素を代入（地覆 ㉓-c）
                        # print(last_found) 丸数字が付いている要素のみ出力
                    elif 'last_found' in locals():  # last_foundが定義されている（要素が代入されている）場合のみ
                        space = last_found.replace("　", " ")
                        # 大文字スペースがあれば小文字に変換
                        second = space.find(" ", space.find(" ") + 1) # 10
                        # 2つ目のスペース位置まで抽出
                        sub_text[i][0] = item + last_found[second:]
                        # item:スペース丸数字の並びがない文字列
                        # last_found:スペース丸数字の並びがある文字列
                        # last_found[second:]:スペースを含めた文字列
                    elif re.match(pattern_start, item): # 文字列が①～㉖で開始するかチェック
                        last_found_circle_number = item # 丸数字の入っている要素を保持
                        sub_text.remove(sub_text[i])
                    else:
                        if last_found_circle_number is not None and not re.search(pattern_anywhere, item):
                            # 要素に丸数字が含まれておらず、直前に丸数字が見つかっている場合
                            sub_text[i][0] += " " + last_found_circle_number  # 要素の末尾に丸数字を追加
                            
                
                print("特記なき損傷")
                for sub_list in sub_text:
                    # サブリストの最初の要素を取得してスペース区切りで分割
                    split_items = sub_list[0].split()
                    
                    # 特記なき損傷の「コンマ付きの損傷」を各要素として保存
                    for in_list in split_items:
                        index_list = ""
                        if re.search(r'[a-z]+,', in_list):
                            print(f"in_list：{in_list}")
                            remove_text = in_list
                            list_index = split_items.index(in_list)
                            print("インデックス")
                            print(list_index) # 2
                            
                            split_list = in_list.split(",")
                            
                    if len(index_list) > 0:
                        split_items[list_index:list_index] = split_list    
                        split_items.remove(remove_text)

                    # 分割した要素から必要なデータを取り出して新しいサブリストに格納
                    header = split_items[0] + " " + split_items[1]  # 例：'主桁 Mg0101'
                    status = split_items[2:]  # 例：'①-d'
                    # photo_number = '写真番号-00'
                    # defpoints = 'defpoints'
                    
                    if "," in status[0]:
                        new_sub_list = [header] + split_list
                    else:
                        new_sub_list = [header] + status
                    
                    extracted_text.append(new_sub_list)

                    new_sub_list.append([str(x), str(y)])
# << ※特記なき損傷の抽出用 ↑ >>
    return extracted_text