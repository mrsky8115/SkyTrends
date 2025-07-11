from django.shortcuts import render,HttpResponse,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from myprojectapp.models import product,cart, orders, PasswordResetOTP, ShippingDetail
from django.views.decorators.csrf import csrf_exempt
import string
import razorpay
import uuid
from .models import cart, orders, ShippingDetail
from django.utils.timezone import now
from django.db.models import Q, F, Sum
import random
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def home(request):
    print("request",request.user.is_authenticated)
    return render(request,'home.html')

def contact_us(request):
    print("request",request.user.is_authenticated)
    return render(request,'contact_us.html')

def about_view(request):
    return render(request, 'aboutus.html')

def index(request):
    query = request.GET.get('q', '')  # URL से search query प्राप्त करें
    if query:
        # Query के आधार पर products को filter करें
        products = product.objects.filter(
            Q(name__icontains=query) |  # Name में search करें
            Q(pdetails__icontains=query) |  # Details में search करें
            Q(cat__icontains=query)  # Category में search करें
        )
    else:
        # Default: सभी active products दिखाएं
        products = product.objects.filter(is_active=True)

    context = {
        'products': products,
        'query': query,  # Search value को retain करने के लिए
    }
    return render(request, 'index.html', context)

def register(request):
    if request.method=='POST':
        uname=request.POST["uname"]
        umail=request.POST["umail"]
        upass=request.POST["upass"]
        ucpass=request.POST["ucpass"]
        context={}
        if uname=="" or umail=="" or upass=="" or ucpass=="":
             context['errmsg']="Field can not be empty" 
             return render(request,'register.html',context)
        elif uname.isnumeric():
            context['errmsg']="Username cannot be a number"
            return render(request, 'register.html',context )
        elif len(upass) < 6:
            context['errmsg'] = "Password must be at least 6 characters long"
            return render(request, 'register.html', context)

        elif upass!=ucpass:
            context['errmsg']="password and confirm password not match"
            return render(request,'register.html',context)    
        
        else:
          try:
            u=User.objects.create_user(password=upass,username=uname,email=umail)
            u.set_password(upass) 
            u.save()
            context['sucess']="User created sucessfully...."
            return render(request,'login.html',context)
          except Exception:
            context['errmsg']="User name already exists"
            return render(request,'register.html',context)    
    else:
        return render(request,'register.html')

def user_login(request):
     if request.method=='POST':
        uname=request.POST["uname"]
        upass=request.POST["upass"]
        context={}
        if uname=="" or upass=="" :
             context['errmsg']="Field can not be empty" 
        else:
            u=authenticate(username=uname,password=upass)
            if u is not None:
                login(request,u)     
                return redirect('/home')
            else:
                context['errmsg']="invalid username and password"
                return render(request,'login.html',context)    
     else :
        return render(request,'login.html')    

def user_logout(request):
    logout(request)             
    return redirect('/home')

@login_required
def profile_view(request):
    # Logged-in user details
    user = request.user

    # Fetch order history for the user
    orders_list = orders.objects.filter(uid=user).order_by('-id')  # Latest orders first
    addresses = ShippingDetail.objects.filter(user=user)  # Fetch addresses for the user

    context = {
        'user': user,
        'orders': orders_list,  # Orders data
        'addresses': addresses
    }
    return render(request, 'profile.html', context)


def productdetails(request,pid):
    p=product.objects.filter(id=pid)
    print(p)
    context={}
    context['products']=p
    return render(request,'productdetails.html',context)  

def addtocart(request, pid):
    if request.user.is_authenticated:
        userid = request.user.id
        u = User.objects.filter(id=userid)
        p = product.objects.filter(id=pid)
        q1 = Q(uid=u[0])
        q2 = Q(pid=p[0])
        c = cart.objects.filter(q1 & q2)
        n = len(c)
        context = {}
        context['products'] = p
        cart_count = cart.objects.filter(uid=u[0]).count()
        context['cart_count'] = cart_count
        
        if n == 1:
            context['msg'] = "Product already exists..."
            return render(request, 'Productdetails.html', context)
        else:
            c = cart.objects.create(uid=u[0], pid=p[0])
            c.save()
            context['success'] = "Product added successfully in cart!..."
            return render(request, 'Productdetails.html', context)
    else:
        return redirect('/login')


# Razorpay Configuration
RAZORPAY_KEY_ID = 'rzp_test_vsTp3lR9NURf3n'
RAZORPAY_KEY_SECRET = 'nUDBVNp2J6rNEvxsem9OE2dg'

def viewcart(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.method == 'POST':
        address_id = request.POST.get('selected_address')
        if address_id:
            try:
                address = ShippingDetail.objects.get(id=address_id, user=request.user)
                request.session['selected_address_id'] = address_id
                return redirect('/makepayment/')
            except ShippingDetail.DoesNotExist:
                messages.error(request, "Invalid address selected")
        else:
            messages.error(request, "Please select a shipping address")

    cart_items = cart.objects.filter(uid=request.user)
    
    if not cart_items.exists():
        return render(request, 'cart.html', {'empty': True})

    total_mrp = sum(item.qty * item.pid.original_price for item in cart_items)
    discount = sum(item.qty * (item.pid.original_price - item.pid.price) for item in cart_items)
    final_amount = sum(item.qty * item.pid.price for item in cart_items)

    addresses = ShippingDetail.objects.filter(user=request.user)

    context = {
        'data': cart_items,
        'total_mrp': total_mrp,
        'discount': discount,
        'final_amount': final_amount,
        'addresses': addresses,
        'selected_address_id': request.session.get('selected_address_id'),
    }
    return render(request, 'cart.html', context)

def makepayment(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if 'selected_address_id' not in request.session:
        messages.error(request, "Please select shipping address first")
        return redirect('/viewcart/')

    cart_items = cart.objects.filter(uid=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('/viewcart/')

    total_amount = sum(item.qty * item.pid.price for item in cart_items)
    request.session['final_amount'] = total_amount
    
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    payment = client.order.create({
        "amount": int(total_amount * 100),
        "currency": "INR",
        "receipt": f"order_{request.user.id}",
    })
    request.session['razorpay_order_id'] = payment['id']

    context = {
        'payment': payment,
        'total_amount': total_amount,
        'RAZORPAY_KEY_ID': RAZORPAY_KEY_ID,
    }
    return render(request, 'pay.html', context)

@csrf_exempt
def confirm_order(request):
    if request.method == 'POST':
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            params = {
                'razorpay_order_id': request.POST.get('razorpay_order_id'),
                'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
                'razorpay_signature': request.POST.get('razorpay_signature')
            }
            client.utility.verify_payment_signature(params)

            address_id = request.session.get('selected_address_id')
            if not address_id:
                raise Exception("No address selected")
                
            address = ShippingDetail.objects.get(id=address_id, user=request.user)
            user = request.user
            cart_items = cart.objects.filter(uid=user)
            
            # Create order and get the instance
            order = orders.objects.create(
                order_id=params['razorpay_order_id'],
                pid=cart_items.first().pid,  # Assuming one product per order
                uid=user,
                qty=sum(item.qty for item in cart_items),
                tracking_id=str(uuid.uuid4())[:8],
                current_status="Order Placed",
                shipping_address=address,
                created_at=now()
            )
            
            # Send email with order details
            sendusermail(request, order)
            
            # Clear cart and session
            cart_items.delete()
            request.session.pop('selected_address_id', None)
            
            # Redirect to order confirmation page
            return redirect('/order_placed/?order_id=' + str(order.id))
            
        except Exception as e:
            print(f"Order Error: {str(e)}")
            messages.error(request, "Order failed. Please try again.")
            return redirect('/viewcart/')
    return HttpResponse("Invalid request")



def sendusermail(request, order):
    try:
        subject = "Order Confirmation - Sky Trends"

        message = f"""
Hello {request.user.username},

Thank you for placing your order with Sky Trends!

🧾 Order Details:
- Product Name: { order.pid.name }
- Price: ₹ { order.pid.price }
- Order ID: {order.order_id}
- Tracking ID: {order.tracking_id}
- Quantity: {order.qty}
- Total Amount Paid: ₹{order.pid.price * order.qty}
- Order Date: {order.created_at.strftime('%d %b %Y')}

📍 Shipping Address:
{order.shipping_address.full_name}
{order.shipping_address.address}
{order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}

We will notify you once your order is shipped.

For any help or queries, feel free to reply to this email or contact us at support@skytrends.in.

Thank you for choosing Sky Trends.
We look forward to serving you again!

Warm regards,  
Sky Trends Team
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def order_placed(request):
    order_id = request.GET.get('order_id')
    order = orders.objects.get(id=order_id, uid=request.user)
    return render(request, 'order_placed.html', {
        'order': order,
        'amount': request.session.get('final_amount', 0)
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

def cancel_order(request, order_id):
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    order = get_object_or_404(orders, id=order_id, uid=request.user)
    
    # Additional check for already cancelled orders
    if order.is_cancelled:
        messages.info(request, "This order has already been cancelled.")
        return redirect('/profile/')
    
    if request.method == 'POST':
        if order.current_status in ['Order Placed'] and not order.is_cancelled:
            order.is_cancelled = True
            order.current_status = 'Cancelled'
            order.cancellation_reason = request.POST.get('reason', '')
            order.cancelled_at = timezone.now()
            order.save()
            
            # Send cancellation email
            send_cancellation_email(request, order)
            
            messages.success(request, "Order cancelled successfully!")
            return redirect('/profile/')
        else:
            messages.error(request, "Order cannot be cancelled now.")
            return redirect('/profile/')
    
    return render(request, 'cancel_order.html', {'order': order})


def send_cancellation_email(request, order):
    try:
        subject = f"Order Cancelled - #{order.order_id}"
        message = f"""
Dear {request.user.username},
        
We want to let you know that your order has been successfully cancelled.
        
Order Details:
                - Order ID: {order.order_id}
                - Product Name: { order.pid.name }
                - Quantity: {order.qty}
                - Total Amount Paid: ₹{order.pid.price * order.qty}

- Reason: {order.cancellation_reason or 'Not specified'}
- Cancellation Date: {order.cancelled_at.strftime('%d %b %Y %H:%M')}


Shipping Address:
                {order.shipping_address.full_name}
                {order.shipping_address.address}
                {order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}


💳 Refund Information:
Since you paid online, your refund will be initiated automatically to the original payment method (e.g., UPI, card, wallet).
Please allow 5-7 working days for the refund to reflect in your account.

📩 Need Help?
If you have any issues or refund delays, feel free to reach out at **support@skytrends.in** or reply to this email.

Thank you for shopping with Sky Trends.  
We hope to serve you again soon.

Warm regards,  
Sky Trends Team

        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Error sending cancellation email: {str(e)}")

# views.py

from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    try:
        send_mail(
            subject="Test Email from Sky Trends",
            message="This is a test email sent from Django.",
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=["mrsky0143@gmail.com"],  # Apna email id daalo check karne ke liye
            fail_silently=False,
        )
        return HttpResponse("✅ Email sent successfully.")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send email: {str(e)}")


def checkout(request):
    if request.method == "POST":
        # Handle form submission here
        if 'address' in request.POST:
            # Save address details
            pass
        elif 'payment' in request.POST:
            # Process payment
            return redirect('order_success')
    
    return render(request, 'checkout.html')


def remove(request,cid):
    c=cart.objects.filter(id=cid) 
    c.delete()
    return redirect('/viewcart')


def remove_address(request, address_id):
    address = ShippingDetail.objects.filter(id=address_id)
    if address.exists():
        address.delete()
    return redirect('/profile')

def update_address(request, aid):
    address = ShippingDetail.objects.get(id=aid)
    if request.method == "POST":
        address.full_name = request.POST.get("full_name")
        address.phone = request.POST.get("phone")
        address.email = request.POST.get("email")
        address.address = request.POST.get("address")
        address.pincode = request.POST.get("pincode")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.country = request.POST.get("country")
        address.save()
        return redirect('/profile')  # Redirect back to the profile page or wherever needed
    return render(request, 'update_address.html', {'address': address})


# Backend view for updating quantity
def update_cart(request):
    if request.method == 'POST':
        cart_id = request.POST.get('cart_id')  # Cart item ID
        quantity = int(request.POST.get('quantity'))  # Updated quantity

        try:
            # Fetch the cart item and update quantity
            cart_item = cart.objects.get(id=cart_id)
            cart_item.qty = quantity
            cart_item.save()
        except cart.DoesNotExist:
            pass

    # Redirect to cart page to refresh the data
    return redirect('/viewcart')

def cart_page(request):
    cart_items = cart.objects.all()

    total_mrp = 0
    discount = 0
    final_amount = 0

    for item in cart_items:
        item.total_price = item.qty * item.pid.price  # Total price per product
        total_mrp += item.qty * item.pid.original_price
        discount += item.qty * (item.pid.original_price - item.pid.price)
        final_amount += item.total_price

    return render(request, 'cart.html', {
        'data': cart_items,
        'total_mrp': total_mrp,
        'discount': discount,
        'final_amount': final_amount
    })

def updateqty(request,qv,cid):
    c=cart.objects.filter(id=cid)
    if qv=='1':
        t=c[0].qty+1
        c.update(qty=t)
    else:
        if c[0].qty>1:
            t=c[0].qty-1
            c.update(qty=t)
        pass
    return redirect('/viewcart') 

from django.db.models import Q

def search_products(request):
    query = request.GET.get('q', '')  # URL से 'q' parameter प्राप्त करें
    products = product.objects.filter(
        Q(name__icontains=query) |  # Product name में search करें
        Q(pdetails__icontains=query) |  # Product details में search करें
        Q(cat__icontains=query)  # Product category में search करें
    ) if query else []  # Query blank हो तो empty list
    return render(request, 'search_results.html', {'products': products, 'query': query})


from .models import cart, orders
from django.views.decorators.csrf import csrf_exempt

# def makepayment(request):
#     # Get user's cart items
#     cart_items = cart.objects.filter(uid=request.user.id)
#     total_amount = sum(item.qty * item.pid.price for item in cart_items)

#     # Convert to paise (Razorpay requires amount in smallest currency unit)
#     total_amount_in_paise = int(total_amount * 100)

#     # Initialize Razorpay client
#     client = razorpay.Client(auth=("rzp_test_vsTp3lR9NURf3n", "nUDBVNp2J6rNEvxsem9OE2dg"))
    
#     # Create Razorpay order
#     payment = client.order.create({
#         "amount": total_amount_in_paise,
#         "currency": "INR",
#         "receipt": f"order_{request.user.id}",
#         "payment_capture": 1  # Auto-capture payment
#     })

#     # Store payment ID in session
#     request.session['razorpay_order_id'] = payment['id']
#     request.session.save()

#     context = {
#         'payment': payment,
#         'cart_items': cart_items,
#         'total_amount': total_amount,
#     }
#     return render(request, 'pay.html', context)



# @csrf_exempt
# def confirm_order(request):
#     if request.method == 'POST':
#         try:
#             # Get payment details
#             razorpay_payment_id = request.POST.get('razorpay_payment_id')
#             razorpay_order_id = request.POST.get('razorpay_order_id')
#             razorpay_signature = request.POST.get('razorpay_signature')

#             # Verify payment
#             client = razorpay.Client(auth=("rzp_test_vsTp3lR9NURf3n", "nUDBVNp2J6rNEvxsem9OE2dg"))
#             params_dict = {
#                 'razorpay_order_id': razorpay_order_id,
#                 'razorpay_payment_id': razorpay_payment_id,
#                 'razorpay_signature': razorpay_signature
#             }
#             client.utility.verify_payment_signature(params_dict)

#             # Get user and cart items
#             user = request.user
#             cart_items = cart.objects.filter(uid=user)
            
#             # Get selected address from session
#             address_id = request.session.get('selected_address_id')
#             address = ShippingDetail.objects.get(id=address_id, user=user)

#             # Create orders
#             for item in cart_items:
#                 orders.objects.create(
#                     order_id=razorpay_order_id,
#                     pid=item.pid,
#                     uid=user,
#                     qty=item.qty,
#                     tracking_id=str(uuid.uuid4())[:8],
#                     current_status="Order Placed",
#                     shipping_address=address  # Save address with order
#                 )

#             # Clear cart
#             cart_items.delete()
#             request.session.pop('selected_address_id', None)

#             # Send email
#             sendusermail(request)
            
#             messages.success(request, "Order placed successfully!")
#             return redirect('home')

#         except Exception as e:
#             print(f"Error in confirm_order: {str(e)}")
#             messages.error(request, "Order failed. Please contact support.")
#             return redirect('viewcart')
#     else:
#         return HttpResponse("Invalid request method")


def catfilter(request,cv):
    # select * from table where cat=1 and is_active=True
    q1=Q(is_active=True)
    q2=Q(cat=cv)
    p=product.objects.filter(q1 & q2)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def sizefilter(request,sf   ):
    q1=Q(is_active=True)
    q2=Q(size=sf)
    p=product.objects.filter(q1 & q2)
    context={}
    context['products']=p
    return render(request,'index.html',context)


def range(request):
    #select * from products where price<=5000 and price>50000 and is_status=True"  
    min=request.GET['min']   #price__gte=min
    max=request.GET['max']   #price__lte=max
    q1=Q(price__gte=min)
    q2=Q(price__lte=max)
    q3=Q(is_active=True)
    p=product.objects.filter(q1 & q2 & q3)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def sort(request,sv):
    if sv=='0':
        col='price'  # sort by price asc order
    else:
        col='-price'        #sort by price desc order
    p=product.objects.filter(is_active=True).order_by(col)
    context={}
    context['products']=p
    return render(request,'index.html',context) 


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        users = User.objects.filter(email=email)

        if not users.exists():
            messages.error(request, "No account found with that email.")
            return render(request, "forgot_password.html")

        for user in users:
            # Generate an OTP
            otp = ''.join(random.choices(string.digits, k=6))
            PasswordResetOTP.objects.update_or_create(user=user, defaults={"otp": otp}) 

    # Send the OTP via email
            send_mail(
                "Password Reset OTP",
                f"Hello {user.username},\n\nYour OTP for resetting the password is: {otp}.\n\nUse this to reset your password.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

        messages.success(request, "An OTP has been sent to your email.")
        return redirect('enter_otp')  # Redirect to the OTP entry page
    return render(request,"Forgot_password.html") 

def enter_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")

        try:
            reset_entry = PasswordResetOTP.objects.get(otp=otp)
            # Save the user ID in session to use it in the reset password view
            request.session['reset_user_id'] = reset_entry.user.id
            return redirect('reset_password')
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, "Invalid or expired OTP.")
            return render(request, "enter_otp.html")

    return render(request, "enter_otp.html")


def reset_password(request):
        user_id = request.session.get('reset_user_id')

        if not user_id:
            messages.error(request, "Unauthorized access. Please restart the process.")
            return redirect('forgot_password')

        try:
            user = User.objects.get(id=user_id)

            if request.method == 'POST':
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')

                if password != confirm_password:
                    messages.error(request, "Passwords do not match.")
                else:
                    user.set_password(password)
                    user.save()
                    del request.session['reset_user_id']  # Clear session after password reset
                    messages.success(request, "Your password has been reset successfully. You can now log in.")
                    return redirect('/login')
        except User.DoesNotExist:
            messages.error(request, "Invalid user.")
            return redirect('forgot_password')

        return render(request, 'reset_password.html')


def track_order(request):
    tracking_id = request.GET.get("tracking_id", None)
    context = {}
    if tracking_id:
        order = orders.objects.filter(tracking_id=tracking_id).first()
        if order:
            context["order"] = order
        else:
            context["error"] = "Invalid Tracking ID"
    return render(request, "track_order.html", context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

def update_order_status(request, order_id):
    # Get the order based on order_id
    order = get_object_or_404(orders, order_id=order_id)
    
    if request.method == "POST":
        # Get the new status from the form
        new_status = request.POST.get("status")
        
        # Update the order status
        order.current_status = new_status
        order.save()  # Save changes to the database
        
        # Success message
        messages.success(request, f"Order status updated to '{new_status}' successfully!")
        
        # Redirect to admin orders page or wherever you want
        return redirect('/admin/myprojectapp/orders/')  # Replace with your desired redirect URL
    
    # Render the update order status form
    return render(request, "update_order_status.html", {"order": order})

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ShippingForm
from .models import ShippingDetail

def shipping_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to save an address.")
        return redirect('/login')  # Redirect to the login page

    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            shipping_detail = form.save(commit=False)
            shipping_detail.user = request.user  # Associate the address with the logged-in user
            shipping_detail.save()
            request.session['address_id'] = shipping_detail.id

            messages.success(request, "Shipping details submitted successfully!")
            return redirect('/viewcart')  # Redirect to the payment page
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        form = ShippingForm()

    return render(request, 'shipping_details.html', {'form': form})








  
