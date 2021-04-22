from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Profile, Order
from .forms import LoginForm, UserRegistrationForm, UserEditForm, OrderForm, ProfileForm
from .utils import userProfile, BTC_price, matchBuy, matchSell


def homepage(request):
    return render(request, 'account/homepage.html')

#Request-1 Endpoint for registration and login
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form
            user = authenticate(request, username=cd.username, password=cd.password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return render(request, 'account/dashboard.html', {'section': 'dashboard'})
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            username = user_form.cleaned_data['username']
            new_user.save()
            userProfile(username) #Request-2 in utils.py
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})

#Request-3 Endpoint for orders creation
@login_required
def new_order(request):
    current_BTC = BTC_price(request)
    if request.method == "POST":
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            profile = Profile.objects.get(user=request.user)
            order.profile = profile
            order.username = request.user.username
            order.published_date = timezone.now()

#Request-4 Try to match the new order with existing orders right after publish (following in utils.py)
            if order.type == ('buy'):
                if order.price <= profile.funds and order.price > 0 and order.quantity > 0:
                    profile.funds -= order.price
                    profile.pending_funds += order.price
                    matchBuy(order, profile, current_BTC)
                else:
                    messages.error(request,'invalid funds amount')
                    return redirect('new_order')
            else:
                if order.quantity <= profile.BTC and order.price > 0 and order.quantity > 0:
                    profile.BTC -= order.quantity
                    profile.pending_BTC += order.quantity
                    matchSell(order, profile, current_BTC)
                else:
                    messages.error(request,'invalid BTCs amount')
                    return redirect('new_order')

            profile.save()
            order.save()
            return redirect('order_list')
    else:
        order_form = OrderForm()
        context = {'order_form': order_form,
                   'current_BTC' : current_BTC}
    return render(request, 'account/new_order.html', context)

#Request-5 Endpoint to view all active orders
@login_required
def order_list(request):
    orders = Order.active.all()
    current_BTC = BTC_price(request)
    context = {'orders': orders,
               'current_BTC': current_BTC}
    return render(request, 'account/order_list.html', context)

#Request-6 endpoint to show the profit for every user
@user_passes_test(lambda u: u.is_staff)
def profit_monitor (request):
    profiles = Profile.objects.all()
    return render(request, 'account/profit_monitor.html', {'profiles':profiles})

#Extra: add funds to account
@login_required
def add_funds(request):
    if request.method == "POST":
        profile_form = ProfileForm(request.POST)
        if profile_form.is_valid():
            toAdd = profile_form.save(commit=False)
            profile = Profile.objects.get(user=request.user)
            profile.funds += toAdd.funds
            profile.save()
            messages.success(request,'Funds added to your account successfully')
            return redirect('dashboard')
    else:
        profile_form = ProfileForm()
    return render(request, 'account/add_funds.html', {'profile_form':profile_form})

#Extra: profile edit page
@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
    return render(request, 'account/edit.html', {'user_form': user_form})

#Extra: personal Dashboard
@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'account/dashboard.html', {'profile': profile})