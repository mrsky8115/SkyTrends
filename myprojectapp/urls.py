from django.urls import path
from myprojectapp import views
from myproject import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),  # Changed to root path
    path('contact-us/', views.contact_us, name='contact_us'),
    path('about-us/', views.about_view, name='about'),
    path('index/', views.index, name='index'),
    path('catfilter/<cv>/', views.catfilter, name='catfilter'),
    path('sizefilter/<sf>/', views.sizefilter, name='sizefilter'),
    path('sort/<sv>/', views.sort, name='sort'),
    path('range/', views.range, name='range'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('productdetails/<int:pid>/', views.productdetails, name='productdetails'),
    path('addcart/<int:pid>/', views.addtocart, name='addtocart'),
    path('viewcart/', views.viewcart, name='viewcart'),
    path('remove/<cid>/', views.remove, name='remove'),
    path('remove-address/<int:address_id>/', views.remove_address, name='remove_address'),
    path('update_address/<int:aid>/', views.update_address, name='update_address'),
    path('updateqty/<qv>/<cid>/', views.updateqty, name='updateqty'),
    path('placeorder/', views.placeorder, name='placeorder'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('search/', views.search_products, name='search'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('makepayment/', views.makepayment, name='makepayment'),
    path('confirm_order/', views.confirm_order, name='confirm_order'),
    path('sendusermail/', views.sendusermail, name='sendusermail'),
    path('order_placed/', views.order_placed, name='order_placed'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('test-email/', views.test_email),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('enterotp/', views.enter_otp, name='enter_otp'),
    path('resetpassword/', views.reset_password, name='reset_password'),
    path('trackorder/', views.track_order, name='track_order'),
    path('updatestatus/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('shipping/', views.shipping_view, name='shipping'),
    path('profile/', views.profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
