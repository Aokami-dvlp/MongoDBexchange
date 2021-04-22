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
    response = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    data = response.json()
    current_BTC = data['bpi']['EUR']['rate_float']
    return current_BTC

#Request-4 Try to match the new order with existing orders right after publish
def matchBuy(order,profile,current_BTC):
    sellOrders = Order.sell.filter(status='active')
    BTCremainings = order.quantity
    fundsRemainings = order.price
    for selling in sellOrders:
        sellerProfile = selling.profile
        seller = Profile.objects.get(user=sellerProfile.user)
        if BTCremainings != 0:
            if BTCremainings >= selling.quantity and (fundsRemainings/BTCremainings) >= (selling.price/selling.quantity):
                BTCremainings -= selling.quantity
                fundsRemainings -= selling.price
                profile.BTC += selling.quantity
                seller.pending_BTC -= selling.quantity
                seller.funds += selling.price
                profile.pending_funds -= selling.price
                profit = selling.price - (selling.quantity*current_BTC)
                seller.profit += profit
                profile.profit -= profit
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


    if order.status == 'active':
        order.quantity = BTCremainings
        order.price = fundsRemainings
        order.save()

def matchSell(order,profile,current_BTC):
    buyOrders = Order.buy.filter(status='active')
    BTCremainings = order.quantity
    unitPrice = order.price/order.quantity
    for buying in buyOrders:
        buyerProfile = buying.profile
        buyer = Profile.objects.get(user=buyerProfile.user)
        if BTCremainings != 0:
            if BTCremainings >= buying.quantity and unitPrice >= (buying.price/buying.quantity):
                BTCremainings -= buying.quantity
                buyer.BTC += buying.quantity
                profile.pending_BTC -= buying.quantity
                profile.funds += buying.price
                buyer.pending_funds -= buying.price
                order.price = BTCremainings * unitPrice
                profit = buying.price - (current_BTC*buying.quantity)
                buyer.profit -= profit
                profile.profit += profit
                buying.status = 'completed'
                profile.save()
                buying.save()
                buyer.save()
                if BTCremainings == 0:
                    order.status = 'completed'
                    order.save()
                    break

    if order.status == 'active':
        order.quantity = BTCremainings
        order.price = BTCremainings * unitPrice
        order.save()