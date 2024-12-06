from .import views
from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

urlpatterns = [
    # << 初期ページ >>
    path('', views.index_view, name='index'),# 使用方法
    # << ファイルアップロード >>
    path("upload/", views.index, name="upload"),# ファイルアップロード
    # << 案件関係 >>
    path('article/', views.ListArticleView.as_view(), name='list-article'),# 案件の一覧
    path('article/create/', views.CreateArticleView.as_view(), name='create-article'),# 案件の登録
    path('article/<int:pk>/detail/', views.DetailArticleView.as_view(), name='detail-article'),# 案件のデータ内容
    path('article/<int:pk>/delete/', views.DeleteArticleView.as_view(), name='delete-article'),# 案件の削除
    path('article/<int:pk>/update/', views.UpdateArticleView.as_view(), name='update-article'),# 案件の更新
    # << 橋梁関係 >>
    path('article/<int:article_pk>/infra/', views.ListInfraView.as_view(), name='list-infra'),# 対象橋梁の一覧
    path('article/<int:article_pk>/infra/create/', views.CreateInfraView.as_view(), name='create-infra'),# 橋梁データの登録
    path('article/<int:article_pk>/infra/<int:pk>/detail/', views.DetailInfraView.as_view(), name='detail-infra'),# 橋梁データの一覧
    path('article/<int:article_pk>/infra/<int:pk>/delete/', views.DeleteInfraView.as_view(), name='delete-infra'),# 橋梁データの削除
    path('article/<int:article_pk>/infra/<int:pk>/update/', views.UpdateInfraView.as_view(), name='update-infra'),# 橋梁データの更新
    # << 名前とアルファベットの登録 >>
    path('article/<int:article_pk>/names/', views.names_list, name='names-list'),# 名前とアルファベットの紐付け
    path('delete_name_entry/<int:entry_id>/', views.delete_name_entry, name='delete_name_entry'),# 登録した名前を削除
    # << 要素番号の登録 >>
    path('article/<int:article_pk>/infra/<int:pk>/number/', views.number_list, name='number-list'),# 要素番号登録
    path('delete_number/<int:article_pk>/infra/<int:pk>/number/<uuid:unique_id>/', views.delete_number, name='delete_number'),# 登録した番号を削除
    path('ajax-get-symbol/', views.get_symbol, name='ajax_get_symbol'),# 部材名と部材記号の紐付け（Ajax）
    # << 損傷写真帳 >>
    path('article/<int:article_pk>/infra/<int:pk>/bridge-table/', views.bridge_table, name='bridge-table'),# 損傷写真帳の作成
    path('article/<int:article_pk>/infra/<int:pk>/bridge-table/upload/', views.upload_picture, name='upload-picture'),# 写真の変更を管理サイトに反映
    #　<< 旗揚げの内容を編集 >>
    path('bridge_table_edit/<int:damage_pk>/<int:table_pk>/', views.edit_report_data, name='edit_report_data'), # 旗揚げの内容を受信
    path('bridge_table_send/<int:damage_pk>/<int:table_pk>/', views.edit_send_data, name='edit_send_data'), # 旗揚げの修正内容を送信
    # << 所見一覧 >>
    path('article/<int:article_pk>/infra/<int:pk>/observations/', views.observations_list, name='observations-list'),# 所見一覧の作成
    path('damage_comment_edit/<int:pk>/', views.damage_comment_edit , name="damage_comment_edit"),# 所見コメントを管理サイトに保存
    path('damage_comment_jadgement_edit/<int:pk>/', views.damage_comment_jadgement_edit , name="damage_comment_jadgement_edit"),# 対策区分を管理サイトに保存
    path('damage_comment_cause_edit/<int:pk>/', views.damage_comment_cause_edit , name="damage_comment_cause_edit"),# 損傷原因を管理サイトに保存
    # << エクセルファイル出力 >>
    path('article/<int:article_pk>/infra/<int:pk>/excel_output/', views.excel_output, name='excel-output'),# Excelファイル出力
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)