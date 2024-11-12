from io import BytesIO
from zipfile import ZipFile
import requests


def download_and_zip_images(image_files):
    """
    リストに含まれるURLから画像をダウンロードし、メモリ上でZIP化する。

    :param image_files: 画像URLまたはImageFieldFileオブジェクトのリスト
    :return: BytesIOオブジェクト（ZIPファイルのバイナリデータ）
    """
    zip_buffer = BytesIO()

    # ZIPファイルをメモリ上で操作
    with ZipFile(zip_buffer, 'w') as zip_file:
        for index, image_file in enumerate(image_files):
            # ImageFieldFileオブジェクトからURLを取得
            if hasattr(image_file, 'url'):
                url = image_file
            elif isinstance(image_file, str):
                url = image_file
            else:
                raise ValueError("Invalid type passed to the function. Expected a URL string or an ImageFieldFile object.")

            # URLから画像を取得
            response = requests.get(url)
            response.raise_for_status()

            # インデックスを用いてファイル名に一意性を与える
            image_name = f"{index+1}.jpg"

            # 画像データをZIP内に追加
            zip_file.writestr(image_name, response.content)

    zip_buffer.seek(0)  # ZIPファイルの先頭にポインターを戻す
    return zip_buffer