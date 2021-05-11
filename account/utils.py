from .models import Profile, Order
from django.contrib.auth.models import User
import random, requests

#Request-2 Assign a random quantity of BTCs (between 1 and 10) to new user
def userProfile(username):
    user = User.objects.get(username=username)
    BTC = round(random.uniform(1,10),2)
    profile = Profile.objects.create(username=username,user=user, BTC=BTC, pending_BTC=0, funds=0, pending_funds=0, profit=0)
    profile.save()

def BTC_price(request):
    url = 'http://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    params = {
        'start': '1',
        'limit': '1',
        'convert': 'EUR'
    }
    headers = {
        'accept': 'application/json',
        'X-CMC_PRO_API_KEY': '002eb6c7-22c2-41b1-9fdd-d2bf5375da4e'
    }
    r = requests.get(url=url, params=params, headers=headers).json()
    BTC = r['data'][0]
    current_BTC = round(BTC['quote']['EUR']['price'], 2)
    return current_BTC

#Request-4 Try to match the new order with existing orders right after publish
def matchBuy(order,profile):
    sellOrders = Order.sell.filter(status='active').order_by('price')
    BTCremainings = order.quantity
    fundsRemainings = order.price * order.quantity
    for selling in sellOrders:
        sellerProfile = selling.profile
        seller = Profile.objects.get(user=sellerProfile.user)
        sellingValue = selling.price * selling.quantity
        if BTCremainings != 0:
            if BTCremainings >= selling.quantity and fundsRemainings >= sellingValue:
                BTCremainings -= selling.quantity
                fundsRemainings -= sellingValue
                profile.BTC += selling.quantity
                seller.pending_BTC -= selling.quantity
                seller.funds += sellingValue
                profile.pending_funds -= order.price * selling.quantity
                profile.funds += (order.price * selling.quantity) - (selling.price * selling.quantity)
                seller.profit += sellingValue
                profile.profit -= sellingValue
                selling.status = 'completed'
                selling.save()
                seller.save()
                if BTCremainings == 0:
                    order.status = 'completed'
                    profile.pending_funds -= fundsRemainings
                    profile.funds += fundsRemainings
                    order.save()
                    profile.save()
                    break
            elif BTCremainings < selling.quantity and order.price >= selling.price:
                selling.quantity -= BTCremainings
                fundsRemainings -= selling.price * BTCremainings
                profile.BTC += BTCremainings
                seller.pending_BTC -= BTCremainings
                seller.funds += selling.price * BTCremainings
                profile.pending_funds -= selling.price * BTCremainings
                seller.profit += selling.price * BTCremainings
                profile.profit -= selling.price * BTCremainings
                order.status = 'completed'
                profile.pending_funds -= fundsRemainings
                profile.funds += fundsRemainings
                order.save()
                seller.save()
                profile.save()
                selling.save()
                break

    if order.status == 'active':
        order.quantity = BTCremainings
        order.save()

def matchSell(order,profile):
    buyOrders = Order.buy.filter(status='active').order_by('-price')
    BTCremainings = order.quantity
    for buying in buyOrders:
        buyerProfile = buying.profile
        buyer = Profile.objects.get(user=buyerProfile.user)
        buyingValue = buying.price * buying.quantity
        if BTCremainings != 0:
            if BTCremainings >= buying.quantity and order.price <= buying.price:
                BTCremainings -= buying.quantity
                buyer.BTC += buying.quantity
                profile.pending_BTC -= buying.quantity
                profile.funds += buyingValue
                buyer.pending_funds -= buyingValue
                buyer.profit -= buyingValue
                profile.profit += buyingValue
                buying.status = 'completed'
                profile.save()
                buying.save()
                buyer.save()
                if BTCremainings == 0:
                    order.status = 'completed'
                    order.save()
                    break
            elif BTCremainings < buying.quantity and order.price <= buying.price:
                buying.quantity -= BTCremainings
                buyer.BTC += BTCremainings
                profile.pending_BTC -= BTCremainings
                profile.funds += buying.price * BTCremainings
                buyer.pending_funds -= buying.price * BTCremainings
                profile.profit += buying.price * BTCremainings
                buyer.profit -= buying.price * BTCremainings
                order.status = 'completed'
                order.save()
                profile.save()
                buying.save()
                buyer.save()
                break

    if order.status == 'active':
        order.quantity = BTCremainings
        order.save()