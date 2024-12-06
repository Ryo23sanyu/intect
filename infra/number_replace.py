import re

# << 要素番号を部材番号に変換する動作 >>
def process_text(text):
    parts = text.split(" : ")
    prefix = parts[0]
    suffixes = parts[1]
    
    items = suffixes.split("/")
    results = [f"{prefix} : {item}" for item in items]
    
    return ", ".join(results)

def remove_alphabet(text):
    result = re.sub(r' [A-Za-z]+(\d+)', r' \1', text)
    return result

def prepare_replacement_lists(result_text):
    matches = re.findall(r"(\S+ \d{2,}),", result_text)
    # 番号が左に来る名称
    main_parts_list_left = ["主桁", "縦桁", "外ケーブル", "ゲルバー部", "PC定着部", "格点", "コンクリート埋込部", ]
    # 番号が右に来る名称
    main_parts_list_right = ["横桁", "橋脚", "橋脚[柱部・壁部]", "橋脚[梁部]", "橋脚[隅角部・接合部]", "橋台", "橋台[胸壁]", "橋台[竪壁]", "橋台[翼壁]", "基礎[フーチング]", "基礎"]
    # 番号が00となる名称
    main_parts_list_zero = ["床版"]

    before_number_list = []
    number_create_list = []
    for parts_name in matches:
        if any(word in parts_name for word in main_parts_list_left):
            left = parts_name.find(" ")
            number2 = parts_name[left+1:]
            number_part = re.search(r'[A-Za-z]*(\d+)', number2).group(1)
            result_parts_name = parts_name[:left] + " " + number_part[:2]
        elif any(word in parts_name for word in main_parts_list_right):
            right = parts_name.find(" ")
            number2 = parts_name[right+1:]
            number_part = re.search(r'[A-Za-z]*(\d+)', number2).group(1)
            result_parts_name = parts_name[:right] + " " + number_part[2:] if len(number_part) < 5 else number_part[2:]
        elif any(word in parts_name for word in main_parts_list_zero):
            right = parts_name.find(" ")
            result_parts_name = parts_name[:right] + " 00"
        else:
            right = parts_name.find(" ")
            result_parts_name = parts_name[:right] + " 00"

        before_number_list.append(parts_name)
        number_create_list.append(result_parts_name)
    return before_number_list, number_create_list

def process_inspection_data(text):
    # 1. スラッシュが含まれている場合の処理
    if "/" in text:
        if ", " in text:
            result = ", ".join([process_text(part.strip()) for part in text.split(",")])
        else:
            result = process_text(text)
    else:
        result = text
    
    # 2. アルファベットの削除
    result_text = remove_alphabet(result.replace(" : ", ","))
    
    # 3. 置換リストを準備
    before_number_list, number_create_list = prepare_replacement_lists(result_text)
    
    # 4. 編集したテキストに置換
    for before, create in zip(before_number_list, number_create_list):
        result_text = result_text.replace(before, create)
    
    return result_text