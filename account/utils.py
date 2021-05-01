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
        sellingUnitPrice = selling.price / selling.quantity
        if BTCremainings != 0:
            if BTCremainings >= selling.quantity and fundsRemainings >= selling.price:
                BTCremainings -= selling.quantity
                fundsRemainings -= selling.price
                profile.BTC += selling.quantity
                seller.pending_BTC -= selling.quantity
                seller.funds += selling.price
                profile.pending_funds -= selling.price
                seller.profit += selling.price
                profile.profit -= selling.price
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
            elif BTCremainings < selling.quantity and fundsRemainings >= (sellingUnitPrice * BTCremainings):
                selling.quantity -= BTCremainings
                selling.price = sellingUnitPrice * selling.quantity
                fundsRemainings -= sellingUnitPrice * BTCremainings
                profile.BTC += BTCremainings
                seller.pending_BTC -= BTCremainings
                seller.funds += sellingUnitPrice * BTCremainings
                profile.pending_funds -= sellingUnitPrice * BTCremainings
                seller.profit += sellingUnitPrice * BTCremainings
                profile.profit -= sellingUnitPrice * BTCremainings
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
        order.price = fundsRemainings
        order.save()

def matchSell(order,profile):
    buyOrders = Order.buy.filter(status='active').order_by('-price')
    BTCremainings = order.quantity
    unitPrice = order.price
    for buying in buyOrders:
        buyerProfile = buying.profile
        buyer = Profile.objects.get(user=buyerProfile.user)
        buyingUnitPrice = buying.price / buying.quantity
        if BTCremainings != 0:
            if BTCremainings >= buying.quantity and unitPrice <= buyingUnitPrice:
                BTCremainings -= buying.quantity
                buyer.BTC += buying.quantity
                profile.pending_BTC -= buying.quantity
                profile.funds += buying.price
                buyer.pending_funds -= buying.price
                order.price = BTCremainings * unitPrice
                buyer.profit -= buying.price
                profile.profit += buying.price
                buying.status = 'completed'
                profile.save()
                buying.save()
                buyer.save()
                if BTCremainings == 0:
                    order.status = 'completed'
                    order.save()
                    break
            elif BTCremainings < buying.quantity and unitPrice <= buyingUnitPrice:
                buying.quantity -= BTCremainings
                buying.price = buyingUnitPrice * buying.quantity
                buyer.BTC += BTCremainings
                profile.pending_BTC -= BTCremainings
                profile.funds += buyingUnitPrice * BTCremainings
                buyer.pending_funds -= buyingUnitPrice * BTCremainings
                profile.profit += buyingUnitPrice * BTCremainings
                buyer.profit -= buyingUnitPrice * BTCremainings
                order.status = 'completed'
                order.save()
                profile.save()
                buying.save()
                buyer.save()
                break

    if order.status == 'active':
        order.quantity = BTCremainings
        order.price = BTCremainings * unitPrice
        order.save()