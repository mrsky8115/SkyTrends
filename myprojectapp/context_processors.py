from .models import cart

def cart_count(request):
    if request.user.is_authenticated:
        count = cart.objects.filter(uid=request.user).count()
        return {'cart_count': count}
    return {'cart_count': 0}


