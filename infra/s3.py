import xlwings as xw

# Excelファイルのパス
file_path = "C:/Users/dbokuka4/Desktop/intect_dxf/bridge_base.xlsm"

# Excelアプリケーションを立ち上げ
app = xw.App(visible=False)  # visible=Falseでバックグラウンドで動作
try:
    # ブックを開く
    wb = app.books.open(file_path)

    # シートを指定して編集する（例：セルA1に"Hello"と入力）
    sheet = wb.sheets['その１']  # シート名を指定
    sheet.range('A1').value = "Hello"

    # 編集したワークブックを新しい名前で保存 (メモリ上に保存する場合は一時ファイルを使う)
    new_file_path = "C:/Users/dbokuka4/Desktop/intect_dxf/edited_base.xlsm"
    wb.save(new_file_path)

    # 作業が完了したらブックを閉じる
    wb.close()
finally:
    # Excelアプリケーションを終了
    app.quit()
