from django.urls import path

from api.views.icon import IconViewSet

urlpatterns = [
    path('api/download_icon/', IconViewSet.as_view({'post': 'download_icon'}), name='download_icon'),
    path('api/remove_bg_img/', IconViewSet.as_view({'post': 'remove_bg_img'}), name='remove_bg_img')
]
