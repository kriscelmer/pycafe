from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort
from .staff import login_required
from .db import MenuItem, StarPointsCustomer, RegularOrder, StarPointsOrder

bp = Blueprint('cashdesk', __name__, url_prefix='/cashdesk')

@bp.route('/')
@login_required
def main_page():
    return render_template('cashdesk/main_page.html')

@bp.route('/menulist', methods=('GET',))
@login_required
def menu_list():
    menu_list = MenuItem.query_all()
    items = []
    for item in menu_list:
        items.append({'id': str(item.id), 'item': item.item, 'category': item.category, 'price': item.price})

    return(jsonify(items), 200)

@bp.route('/spcustomer', methods=('GET', 'POST', 'PUT'))
@login_required
def spcustomer():
    nick = request.args.get('nick', '')
    if nick == '':
        return("Star Points Customer nickname is required!", 400)

    name = request.args.get('name', '')
    email = request.args.get('email', '')
    add_points = request.args.get('add', '')
    if request.method == 'GET':
        sp_customer = StarPointsCustomer.query_one(nick=nick)
        if sp_customer == None:
            return("No Star Points Customer with nick {}!".format(nick), 404)
        return(jsonify({'nick': sp_customer.nick, 'name': sp_customer.name, 'email': sp_customer.email, 'points': sp_customer.points}), 200)

    elif request.method == 'POST':
        if name == '':
            return("Star Points Customer name is required!", 400)
        elif email == '':
            return("Star Points Customer e-mail address is required!", 400)
        sp_customer = StarPointsCustomer.query_one(nick=nick)
        if sp_customer == None:
            sp_customer = StarPointsCustomer(nick=nick, name=name, email=email)
            if sp_customer.save():
                return("Star Points Customer {} created".format(nick), 200)
            else:
                return("Internal Database error!", 500)
        else:
            return("Star Points Customer with nick '{}' already exits!".format(nick), 400)

    elif request.method == 'PUT':
        sp_customer = StarPointsCustomer.query_one(nick=nick)
        if sp_customer == None:
            return("No Star Points Customer with nick {}!".format(nick), 404)
        if add_points == '':
            return("Add points argument is required!", 400)
        try:
            i = int(add_points)
        except:
            return("Add points argument must be an Integer!", 400)
        sp_customer.points += i
        if sp_customer.save():
            return("{} points added for Star Points Customer {}".format(i,nick), 200)
        else:
            return("Internal Database error!", 500)
    else:
        return("Unsupported request method", 400)

@bp.route('/order', methods=('POST',))
@login_required
def order():
    total = float(request.args.get('total', 0.0))
    nick = request.args.get('nick', '')
    points = int(request.args.get('points', 0))
    order_json = request.data.decode('utf-8')
    cashier_id = g.user.id

    sp_customer = None
    customer_id = 0
    if nick != '':
        sp_customer = StarPointsCustomer.query_one(nick=nick)
        if sp_customer:
            customer_id = sp_customer.id

    order = RegularOrder(total=total, cashier_id=cashier_id, customer_id=customer_id, points=points, order_json=order_json)

    if order.save():
        if sp_customer:
            sp_customer.points += points
            sp_customer.cumulative += points
            if not sp_customer.save():
                print("Failed to add order points to Star Points Customer...")
        return("Order registered", 200)
    else:
        return("Failed to save the order!", 500)

@bp.route('/sporder', methods=('POST',))
@login_required
def sporder():
    nick = request.args.get('nick', '')
    points = int(request.args.get('pointstaken', 0))
    order_json = request.data.decode('utf-8')
    cashier_id = g.user.id

    sp_customer = None
    customer_id = 0
    if nick != '':
        sp_customer = StarPointsCustomer.query_one(nick=nick)
        if sp_customer:
            customer_id = sp_customer.id
        else:
            return("Star Points Customer with nick={} not found!".format(nick), 404)
    else:
        return("Star Points Customer nick is required!", 400)

    if points <=0:
        return("Star Points Order 'pointstaken' must be greater than 0!", 400)

    if sp_customer.points < points:
        return("Star Points Customer {} doesn't have enough points!", 400)

    if order_json == '':
        return("Order JSON cannot be empty!", 400)

    order = StarPointsOrder(points=points, order_json=order_json, cashier_id=cashier_id, customer_id=customer_id)

    if order.save():
        if sp_customer:
            sp_customer.points -= points
            if not sp_customer.save():
                print("Failed to add order points to Star Points Customer...")
        return("Order registered", 200)
    else:
        return("Failed to save the order!", 500)
