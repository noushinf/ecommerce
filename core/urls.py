from django.urls import path
from core import views
from django.views.decorators.cache import cache_page
from django.conf import settings

from core.views import ProductListview

urlpatterns = [
    # path('', cache_page(settings.REDIS_CASHED_TIME)(ProductListview.as_view()),name='index'),
    path('', views.index, name='index'),
    path('add_producut', views.add_product, name='add_product'),
    path('product_desc/<int:pk>', views.product_dec, name='product_desc'),
    path('add_to_card/<int:pk>', views.add_to_card, name='add_to_card'),
    path('orderlist', views.orderlist, name='orderlist'),
    path('add_item/<int:pk>', views.add_item, name='add_item'),
    path('remove_item/<int:pk>', views.remove_item, name='remove_item'),
    path('checkout_page', views.checkout_page, name='checkout_page'),
    path('payment', views.payment, name='payment'),
    path('handlerequest', views.handlerequest, name='handlerequest'),
    path("invoice", views.invoice, name='invoice'),
    path("render_pdf_view", views.render_pdf_view, name='render_pdf_view'),

]
