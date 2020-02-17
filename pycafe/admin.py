import click
from flask.cli import with_appcontext
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
from werkzeug.security import generate_password_hash
from .db import get_db, StaffUser, MenuItem, RegularOrder, StarPointsCustomer, StarPointsOrder
from .staff import admin_login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Create Staff user with Admin role
@click.command('create-admin', short_help='create Staff user with Admin role')
@with_appcontext
@click.argument('username', nargs=1)
def create_admin(username):
    click.echo('Creating Staff user {} with Admin role...'.format(username))
    user = StaffUser.query_one(username=username)
    if user:
        click.echo('Staff user {} already exists!'.format(username))
    else:
        email = click.prompt('Enter e-mail address', confirmation_prompt=True)
        password = click.prompt('Enter password', hide_input=True, confirmation_prompt=True)
        user = StaffUser(username=username, email=email, password=generate_password_hash(password), is_admin=True)
        if user.save():
            click.echo('Created Admin user {}'.format(username))
        else:
            click.echo('Database error while creating Admin Staff user {}'.format(username))

# Unlock Staff user
@click.command('reset-user', short_help='Unlock Staff user account')
@with_appcontext
@click.argument('username', nargs=1)
def reset_user(username):
    click.echo('Reseting Staff user {} ...'.format(username))
    user = StaffUser.query_one(username=username)
    if user is None:
        click.echo('No such Staff user {}!'.format(username))
    else:
        password = click.prompt('Please enter new password', hide_input=True, confirmation_prompt=True)
        if password == '':
            click.echo('Password cannot be empty!')
            return
        user.password = generate_password_hash(password)
        user.failed_login_attempts = 0
        user.locked_since = "0000-00-00 00:00:00"
        if user.save():
            click.echo('Staff user {} account is reset now'.format(username))
        else:
            click.echo('Database error while updating Staff user {}'.format(username))


# Delete Staff user from database
@click.command('delete-user', short_help='delete Staff user from database based on user ID')
@with_appcontext
@click.argument('userid', nargs=1)
def delete_user(userid):
    click.echo('Deleting Staff user with ID {}...'.format(userid))
    users = StaffUser.query_all(id=userid)
    if len(users) > 0:
        user = users[0]
        username = user.username
        if click.confirm('Please confirm deletion of Staff user "{}"'.format(username)):
            if user.delete():
                click.echo('Staff user "{}" deleted.'.format(username))
            else:
                click.echo('Cannot delete Staff user id={}, username={}! Database error.'.format(userid, username))
        else:
            click.echo("Staff user deletion aborted.")
    else:
        click.echo('No Staff user with ID={} in database!'.format(userid))


# List Staff users in database
@click.command('list-users', short_help='list Staff users in database')
@with_appcontext
def list_users():
    click.echo('Listing all Staff users in database...')
    users = StaffUser.query_all()
    print('{:>7} | {:15.15} | {:15:15} | {:^10} | {:^10} | {:>10} | {:^10}'.format('User ID', 'Username', 'E-mail', 'Is Admin?', 'Is Active?', 'Failed Log', 'Lckd Since'))
    for user in users:
        print('{:>7} | {:15.15} | {:15:15} | {:^10} | {:^10} | {:>10} | {:^10}'.format(user.id, user.username, user.email, user.is_admin, user.is_active, user.failed_login_attempts, user.locked_since))

# List Regular Orders in database
@click.command('list-orders', short_help='list Regular orders in database')
@with_appcontext
def list_orders():
    click.echo('Listing all Regular orders in database...')
    orders = RegularOrder.query_all()
    print('{:>10} | {:30.30} | {:^8} | {:^10} | {:^10} | {:>10}'.format('Order ID', 'Order date', 'Total', 'Cashier', 'Customer', 'Points'))
    for order in orders:
        print('{:>10} | {:30.30} | {:^8} | {:^10} | {:^10} | {:>10}'.format(order.id, order.order_date, order.total, order.cashier_id, order.customer_id, order.points))

# List Star Points Orders in database
@click.command('list-sporders', short_help='list Star Points orders in database')
@with_appcontext
def list_sporders():
    click.echo('Listing all Star Points orders in database...')
    orders = StarPointsOrder.query_all()
    print('{:>10} | {:30.30} | {:^8} | {:^10} | {:^10}'.format('Order ID', 'Created', 'Points', 'Cashier', 'Customer'))
    for order in orders:
        print('{:>10} | {:30} | {:^8} | {:^10} | {:^10}'.format(order.id, order.created, order.points, order.cashier_id, order.customer_id))


def init_app(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(reset_user)
    app.cli.add_command(delete_user)
    app.cli.add_command(list_users)
    app.cli.add_command(list_orders)
    app.cli.add_command(list_sporders)

# Executed before processing each request, fetches 'user' from 'session'
@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = StaffUser.query_one(username=username)

# Main landing page (index) for Admin staff users
@bp.route('/')
@admin_login_required
def main_page():
    return render_template('admin/main_page.html')

@bp.route('/menu', methods=('GET', 'POST', 'PUT', 'DELETE'))
@admin_login_required
def menu():
    if request.method == 'GET':
        menu_list = MenuItem.query_all()
        items = []
        for item in menu_list:
            items.append({'id': str(item.id), 'item': item.item, 'category': item.category, 'price': item.price})

        return jsonify({'menu': items, 'categories': MenuItem.CATEGORIES})

    elif request.method == 'POST':
        item = request.args.get('item', None)
        category = request.args.get('category', None)
        price = request.args.get('price', None)

        menu_item = MenuItem.query_one(item=item)
        error = None

        if not item:
            error = 'Item name is required!'
        elif not category in MenuItem.CATEGORIES:
            error = 'Valid Category is required!'
        elif not ((float(price) >= 0.0) & (float(price) <= 99.99)):
            error = 'Price must be >= 0.0 and <= 99.99'
        elif menu_item is not None:
            error = 'Menu item {} already exists!'.format(item)
        else:
            menu_item = MenuItem(item=item)

        if error is None:
            menu_item.category = category
            menu_item.price = price
            if menu_item.save():
                return(str(menu_item.id), 200)
            else:
                return("Menu item Database save failure!", 500)
        else:
            return(error, 400)

    elif request.method == 'PUT':
        itemid = request.args.get('id', '')
        item = request.args.get('item', '')
        category = request.args.get('category', '')
        price = request.args.get('price', '')

        if itemid == '' or itemid == '0':
            return('Menu Item ID required!', 400)
        elif item == '':
            return('Item name is required!', 400)
        elif category == '':
            return('Category is required!', 400)
        elif not category in MenuItem.CATEGORIES:
            return('Unrecognized category {}!'.format(category))
        elif price == '':
            return('Price is requested!', 400)
        elif float(price) < 0.0:
            return('Price must be >=0.0')
        elif float(price) > 99.99:
            return('Price must be <=99.99')

        menu_item = MenuItem.query_one(id=itemid)
        if menu_item is None:
            return('No Menu item with ID {}!'.format(itemid), 404)

        menu_item.item = item
        menu_item.category = category
        menu_item.price = price

        if menu_item.save():
            return ('Menu item {} is updated'.format(item), 200)
        else:
            return ('Menu Item Database save failure!', 500)

    elif request.method == 'DELETE':
        itemid = request.args.get('id', '')
        menu_item = MenuItem.query_one(id=itemid)

        if menu_item:
            itemname = menu_item.item
            if menu_item.delete():
                return ("Menu item {} permanently removed".format(itemname), 200)
            else:
                return ("Falied to delete Database record of menu item {}!".format(itemname), 500)
        else:
            return ("No such menu item in Database!", 404)

    else:
        return("Unsupported HTTP Method!", 400)

@bp.route('/staff', methods=('GET', 'POST', 'PUT', 'DELETE'))
@admin_login_required
def staff():
    if request.method == 'GET':
        # List Staff users in database
        staff_list = StaffUser.query_all();
        users = []
        for user in staff_list:
            users.append({'id': str(user.id), 'username': user.username, 'email': user.email, 'is_admin': user.is_admin, 'is_active': user.is_active, 'locked': user.is_locked()})
        return jsonify(users)

    elif request.method == 'POST':
        # create new Staff user
        username = request.args.get('username', '')
        email = request.args.get('email', '')
        password = request.args.get('password', '')
        is_admin = request.args.get('is_admin', 'false') == 'true'

        if username == '':
            return('Username is required!', 400)
        elif email == '':
            return('E-mail address is required!', 400)
        elif password == '':
            return('Password is required!', 400)

        staff_user = StaffUser.query_one(username=username)
        if staff_user is None:
            staff_user = StaffUser(username=username, email=email, password=generate_password_hash(password), is_admin=is_admin)

            if staff_user.save():
                return (str(staff_user.id), 200)
            else:
                return ('Staff Users Database save failure!', 500)
        else:
            return('Staff user {} already exists!'.format(username), 400)

    elif request.method == 'PUT':
        # update existing Staff user
        userid = request.args.get('id', '')
        username = request.args.get('username', '')
        email = request.args.get('email', '')
        password = request.args.get('password', '')
        is_admin = request.args.get('is_admin', '')
        is_active = request.args.get('is_active', '')
        unlock = request.args.get('unlock', '')

        if userid == '' or userid == '0':
            return('User ID required!', 400)

        staff_users = StaffUser.query_all(id=userid)
        if len(staff_users) == 0:
            return('No user with ID {}!'.format(userid), 404)
        else:
            staff_user = staff_users[0]

        if username != '':
            staff_user.username = username
        if email != '':
            staff_user.email = email
        if password != '':
            staff_user.password = generate_password_hash(password)
        if is_admin != '':
            staff_user.is_admin = is_admin == 'true'
        if is_active != '':
            staff_user.is_active = is_active == 'true'
        if unlock == 'true':
            staff_user.failed_login_attempts = 0
            staff_user.locked_since = "0000-00-00 00:00:00"

        if staff_user.save():
            return ('Staff user {} is saved'.format(username), 200)
        else:
            return ('Staff Users Database save failure!', 500)

    elif request.method == 'DELETE':
        # delete deactivated Staff user from database
        userid = request.args.get('id', '')
        users = StaffUser.query_all(id=userid)
        if len(users) > 0:
            if users[0].is_active:
                return("Cannot delete active Staff user!", 400)
            username = users[0].username
            if users[0].delete():
                return("Staff user {} deleted".format(username), 200)
            else:
                return("Failed to delete user {} from database!", 500)
        else:
            return ("No such staff user in Database!", 404)
    else:
        return("Unsupported HTTP Method!", 400)

@bp.route('/spcustomers', methods=('GET', 'PUT'))
@admin_login_required
def spcustomers():
    if request.method == 'GET':
        spcustomers_list = StarPointsCustomer.query_all()
        spcustomers = []
        for spcustomer in spcustomers_list:
            spcustomers.append({'id': str(spcustomer.id), 'nick': spcustomer.nick, 'name': spcustomer.name, 'email': spcustomer.email, 'points': str(spcustomer.points), 'cumulative': str(spcustomer.cumulative)})

        return jsonify(spcustomers)

    elif request.method == 'PUT':
        id = request.args.get('id', '')
        name = request.args.get('name', '-')
        nick = request.args.get('nick', '-')
        email = request.args.get('email', '-')
        points = request.args.get('points', '-')

        if id == '' or id == '0':
            return('Star Points Customer ID required!', 400)

        if nick == '':
            return("Star Points Customer nick cannot be empty!", 400)

        spcustomer = StarPointsCustomer.query_one(id=id)
        if spcustomer == None:
            return('No Star points Customer with ID={}!'.format(id), 404)

        if nick != '-':
            spcustomer.nick = nick

        if name != '-':
            spcustomer.name = name

        if email != '-':
            spcustomer.email = email

        if points != '-':
            spcustomer.points = int(points)

        spcustomer.nick = nick

        if spcustomer.save():
            return('Star Points Customer updated', 200)
        else:
            return('Failed to update Star Points Customer. Database error!', 500)

@bp.route('/sporders', methods=('GET',))
@admin_login_required
def sporders():
    query_args = {}
    cashierid = request.args.get('cashier_id','')
    if cashierid != '':
        query_args['cashier_id'] = cashierid

    cashier_name = request.args.get('cashier', '')
    if cashier_name != '':
        cashier = StaffUser.query_one(username=cashier_name)
        if cashier is None:
            return("Staff user name '{}' not found!".format(cashier_name), 404)
        query_args['cashier_id'] = str(cashier.id)

    customer_nick = request.args.get('customer', '')
    if customer_nick != '':
        customer = StarPointsCustomer.query_one(nick=customer_nick)
        if customer is None:
            return("Star Points customer named '{}' fot found!".format(customer_nick), 404)
        query_args['customer_id'] = str(customer.id)

    date_le = request.args.get('date_le', '')
    if date_le != '':
        query_args['date_le'] = date_le

    date_ge = request.args.get('date_ge', '')
    if date_ge != '':
        query_args['date_ge'] = date_ge

    order_list = StarPointsOrder.query_all(**query_args);
    if len(order_list) > 0:
        staff = StaffUser.query_all()
        staff_usernames = {}
        for user in staff:
            staff_usernames[user.id] = user.username

        spcustomers = StarPointsCustomer.query_all()
        sp_nicks = {}
        sp_nicks[0] = ''
        for user in spcustomers:
            sp_nicks[user.id] = user.nick

    orders = []
    for order in order_list:
        orders.append({'id': str(order.id), 'cashier': staff_usernames[order.cashier_id], 'customer': sp_nicks[order.customer_id], 'points': order.points, 'created': order.created, 'order_json': order.order_json})
    return jsonify(orders)


@bp.route('/orders', methods=('GET',))
@admin_login_required
def orders():
    query_args = {}

    cashier_id = request.args.get('cashier_id', '')
    if cashier_id != '':
        query_args['cashier_id'] = cashier_id

    points_le = request.args.get('points_le', '')
    if points_le != '':
        query_args['points_le'] = points_le

    points_ge = request.args.get('points_ge', '')
    if points_ge != '':
        query_args['points_ge'] = points_ge

    customer_nick = request.args.get('customer', '')
    if customer_nick != '':
        customer = StarPointsCustomer.query_one(nick=customer_nick)
        if customer is None:
            return("Star Points customer named '{}' fot found!".format(customer_nick), 404)
        query_args['customer_id'] = str(customer.id)

    date_le = request.args.get('date_le', '')
    if date_le != '':
        query_args['date_le'] = date_le

    date_ge = request.args.get('date_ge', '')
    if date_ge != '':
        query_args['date_ge'] = date_ge

    cashier_name = request.args.get('cashier', '')
    if cashier_name != '':
        cashier = StaffUser.query_one(username=cashier_name)
        if cashier is None:
            return("Staff user name '{}' not found!".format(cashier_name), 404)
        query_args['cashier_id'] = str(cashier.id)

    order_list = RegularOrder.query_all(**query_args);
    if len(order_list) > 0:
        staff = StaffUser.query_all()
        staff_usernames = {}
        for user in staff:
            staff_usernames[user.id] = user.username

        spcustomers = StarPointsCustomer.query_all()
        sp_nicks = {}
        sp_nicks[0] = ''
        for user in spcustomers:
            sp_nicks[user.id] = user.nick

    orders = []
    for order in order_list:
        orders.append({'id': str(order.id), 'total': order.total, 'cashier': staff_usernames[order.cashier_id], 'customer': sp_nicks[order.customer_id], 'points': order.points, 'order_date': order.order_date, 'order_json': order.order_json})
    return jsonify(orders)
