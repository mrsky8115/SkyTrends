from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.  
class product(models.Model):
    CAT = ((1, 'T-Shirts'), (2, 'Shirts'), (3, 'Jeans'), (4, 'Trousers'), (5, 'Boxers'), (6, 'Polo T-shirt'), (7, 'OverSized T-shirt'))
    SIZE = ((1, 'S'), (2, 'M'), (3, 'L'), (4, 'XL'), (5, 'XXL'), (6, '28'), (7, '30'), (8, '32'))
    TYPE = ((1, 'Top Wear'), (2, 'Bottom Wear'))

    name = models.CharField(max_length=50, verbose_name='Product Name')
    price = models.FloatField(verbose_name='Product Price')
    original_price = models.FloatField(verbose_name='Original Price', default=0.0)  # New Field
    pdetails = models.CharField(max_length=100)
    type = models.IntegerField(verbose_name='Type', choices=TYPE, default=1)
    cat = models.IntegerField(verbose_name='Product Category', choices=CAT)
    size = models.IntegerField(verbose_name='Size', choices=SIZE)
    is_active = models.BooleanField(default=True, verbose_name='Available')
    pimage = models.ImageField(upload_to='image')

    # Method to calculate discount percentage
    def discount_percentage(self):
        if self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount)
        return 0

    def saveprice (self):
        if self.original_price > self.price:
            save = (self.original_price - self.price)
            return round(save)
        return 0


    def __str__(self):
        return self.name
class cart(models.Model):
    uid=models.ForeignKey(User,on_delete=models.CASCADE,db_column="uid")   
    pid=models.ForeignKey(product,on_delete=models.CASCADE,db_column="pid") 
    qty=models.IntegerField(default=1) 

    def total_price(self):
        return self.pid.price * self.qty

    def __str__(self):
        return f"{self.pid.name} x {self.qty}"

class ShippingDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shipping_details")
    full_name = models.CharField(max_length=30, null=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.CharField(max_length=255, default="Not Provided")
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=20, default='India')
    Created_at = models.DateTimeField(auto_now=True)  # Automatically set when created
    Updated_at = models.DateTimeField(auto_now=True)  # Automatically update when modified


    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state} {self.address}"
    

class orders(models.Model):
    STATUS_CHOICES = [
        ('Order Placed', 'Order Placed'),
        ('Dispatched', 'Dispatched'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=50)
    tracking_id = models.CharField(max_length=20, unique=True, blank=True)
    current_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='Order Placed')
    last_updated = models.DateTimeField(auto_now=True)
    uid = models.ForeignKey(User, on_delete=models.CASCADE, db_column="uid")   
    pid = models.ForeignKey(product, on_delete=models.CASCADE, db_column="pid")
    qty = models.IntegerField(default=1)
    shipping_address = models.ForeignKey(ShippingDetail, on_delete=models.SET_NULL, null=True, blank=True)  # Added this line
    created_at = models.DateTimeField(auto_now_add=True)  # Added creation timestamp
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order_id} by {self.uid.username} for {self.pid.name}"
    
class PasswordResetOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from datetime import timedelta, timezone
        return self.created_at >= timezone.now() - timedelta(minutes=10)
    
    def cart_count(request):
        if request.user.is_authenticated:
            count = cart.objects.filter(uid=request.user).count()
            return {'cart_count': count}
        return {'cart_count': 0}

