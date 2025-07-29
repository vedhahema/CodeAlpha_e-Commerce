from django.shortcuts import render
from shop . forms import CustomUserForm
from . models import *
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

def home(request):
    products=product.objects.filter(trending=1)
    return render(request,"shop/index.html",{"products":products})
def cart_page(request):
    if request.user.is_authenticated:
        Cart=cart.objects.filter(user=request.user)
        return render(request,"shop/cart.html",{"cart":Cart})
    else:
        return redirect("/")

def fav_page(request):
    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        if request.user.is_authenticated:
            data=json.load(request)
            product_id=data['pid']
            product_status=product.objects.get(id=product_id)
            if product_status:
                if favourite.objects.filter(user=request.user.id,product_id=product_id):
                    return JsonResponse({'status':'Product add already success'}, status=200)
                else:
                    favourite.objects.create(user=request.user,product_id=product_id,)
                    return JsonResponse({'status' : 'Product Added To Favourite'}, status=200)
                
        else:       
         return JsonResponse({'status':'login to add favourite'}, status=200)
    else:
        return JsonResponse({'status':'invalid Access'},status=200)

def favviewpage(request):
    if request.user.is_authenticated:
        fav=favourite.objects.filter(user=request.user)
        return render(request,"shop/fav.html",{"fav":fav})
    else:
        return redirect("/")
    
def add_to_cart(request):
    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        if request.user.is_authenticated:
            data=json.loads(request.body)
            product_qty=data['product_qty']
            product_id=data['pid']
            product_status=product.objects.get(id=product_id)
            if product_status:
                if cart.objects.filter(user=request.user.id,product_id=product_id):
                 return JsonResponse({'status':'Product add to cart success'}, status=200)
                else:
                    if product_status.quantity>=product_qty:
                        cart.objects.create(user=request.user,product_id=product_id,product_qty=product_qty)
                        return JsonResponse({'status':'product add to cart sucess'}, status=200)
                    else:
                        return JsonResponse({'status':'product stock not available'}, status=200)
        else:       
         return JsonResponse({'status':'login to add cart'}, status=200)
    else:
        return JsonResponse({'status':'invalid Access'}, status=200)   

def logout_page(request):
    if request.user.is_authenticated:
       logout(request)
       messages.success(request,"logged out successfully")
    return redirect("home")

def login_page(request):
    if request.user.is_authenticated:
      return redirect("/")
    else:
        if request.method=='POST':
            name=request.POST.get('username')
            password=request.POST.get('password')
            user=authenticate(request,username=name,password=password)
            if user is not None:
                login(request,user)
                messages.success(request,"Login Successful")
                return redirect('home')
            else:
                messages.error(request,"Invalid Credentials")
                return redirect('login')
        return render(request,"shop/login.html")

def register(request):
    form=CustomUserForm()
    if request.method=='POST':
        form=CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"resgistration success you can login now..!")
            return redirect('/login')
    return render(request,"shop/register.html ",{"forms":form})

def collections(request):
    catagory=category.objects.filter(status=0)
    return render(request,"shop/collections.html",{"catagory":catagory})

def collectionview(request,name):
    if(category.objects.filter(name=name,status=0)):
        products=product.objects.filter(category__name=name)
        return render(request,"shop/products/index.html",{"products":products,"category_name":name})
    else:
        messages.warning(request,"No Such Category Found")
        return redirect('collections')
def product_details(request,cname,pname):
    if(category.objects.filter(name=cname,status=0)):
       if(product.objects.filter(name=pname, status=0)):
           products=product.objects.filter(name=pname,status=0).first()
           return render(request,"shop/products/product_details.html",{"products":products})
    else:
       messages.error(request,"no such category found")
       return redirect('collections')
    

def remove_cart(request, cid):
    cartitem=cart.objects.get(id=cid)
    cartitem.delete()
    return redirect("/cart")


def remove_fav(request, fid):
    favitem=favourite.objects.get(id=fid)
    favitem.delete()
    return redirect("/favviewpage")


def buy_now_view(request, pid, qty):
    if not request.user.is_authenticated:
        messages.error(request, "Login to continue.")
        return redirect('login')

    try:
        product_obj = product.objects.get(id=pid)
    except product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('home')

    if product_obj.quantity < int(qty):
        messages.warning(request, "Product stock not available.")
        return redirect('product_details', cname=product_obj.category.name, pname=product_obj.name)

    total = product_obj.selling_price * int(qty)

    return render(request, 'shop/checkout.html', {
        'product': product_obj,
        'qty': qty,
        'total': total
    })
@csrf_exempt
def place_order(request):
    if request.method == "POST" and request.user.is_authenticated:
        pid = request.POST.get('product_id')
        qty = int(request.POST.get('qty'))
        total_price = float(request.POST.get('total_price'))

        product_obj = product.objects.get(id=pid)

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status='Confirmed'
        )
        OrderItem.objects.create(
            order=order,
            product=product_obj,
            quantity=qty,
            price=product_obj.selling_price
        )

        product_obj.quantity -= qty
        product_obj.save()

        messages.success(request, "Order placed successfully.")
        return redirect('home')
    return redirect('home')
