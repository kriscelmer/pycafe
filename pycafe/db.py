import sqlite3
import click
import datetime
from flask import g
from flask import current_app as app
from flask.cli import with_appcontext

class StaffUser:

    id = 0

    def __init__(self, username, id=0, password='', email='', is_admin=False, is_active=True, failed_login_attempts=0, locked_since="0000-00-00 00:00:00"):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.is_admin = is_admin
        self.is_active = is_active
        self.failed_login_attempts = failed_login_attempts
        self.locked_since = locked_since

    def read(self):
        db = get_db()
        db_row = db.execute(
            'SELECT * FROM user WHERE username = ?', (self.username,)
        ).fetchone()
        if db_row is None:
            self.id = None
            return None
        else:
            self.id = db_row['id']
            self.password = db_row['password']
            self.email = db_row['email']
            self.is_admin = db_row['is_admin']
            self.is_active = db_row['is_active']
            self.failed_login_attempts = db_row['failed_login_attempts']
            self.locked_since = db_row['locked_since']
            return self

    def save(self):
        save_username = self.username
        save_password = self.password
        save_email = self.email
        save_is_admin = self.is_admin
        save_is_active = self.is_active
        save_failed_login_attempts = self.failed_login_attempts
        save_locked_since = self.locked_since

        db = get_db()
        if self.id > 0:
            db.execute(
                'UPDATE user SET username = ?, password = ?, email = ?, is_admin = ?, is_active = ?, failed_login_attempts = ?, locked_since = ? WHERE id = ?',
                (self.username, self.password, self.email, self.is_admin, self.is_active, self.failed_login_attempts, self.locked_since, self.id)
            )
        else:
            db.execute(
                'INSERT INTO user (username, password, email, is_admin, is_active, failed_login_attempts, locked_since) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (self.username, self.password, self.email, self.is_admin, self.is_active, self.failed_login_attempts, self.locked_since)
            )
        db.commit()

        if self.read():
            if self.username != save_username :
                return False
            elif self.password != save_password :
                return False
            elif self.email != save_email:
                return False
            elif self.is_admin != save_is_admin :
                return False
            elif self.is_active != save_is_active :
                return False
            elif self.failed_login_attempts != save_failed_login_attempts:
                return False
            elif self.locked_since != save_locked_since:
                return False
            else:
                return True
        else:
            return False

    def delete(self):
        if self.id > 0:
            # if it has 'id', then it exists in Database
            db = get_db()
            db.execute(
                'DELETE FROM user WHERE id = ?', (self.id,)
            )
            db.commit()

        if self.read():
        # record still exists in Database -> delete has failed!
            return False
        else:
            return True

    def is_locked(self):
        # Staff User account is locked when 'locked_since' is greater or equal than now - ACCOUNT_LOCK_PERIOD_SECONDS
        now_minus_lock_period = datetime.datetime.now() - datetime.timedelta(seconds=app.config['ACCOUNT_LOCK_PERIOD_SECONDS'])
        return self.locked_since >= now_minus_lock_period.isoformat(sep=' ', timespec='seconds')

    def query_all(**selectors):
        # query through all Staff Users
        select_string = "SELECT * FROM user"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'username' in selectors:
            if num_selectors > 0:
                select_string += " AND username = '"+selectors['username']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE username = '"+selectors['username']+"'"
                num_selectors = 1

        if 'password' in selectors:
            if num_selectors > 0:
                select_string += " AND password = '"+selectors['password']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE password = '"+selectors['password']+"'"
                num_selectors = 1

        if 'email' in selectors:
            if num_selectors > 0:
                select_string += " AND email = '"+selectors['email']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE email = '"+selectors['email']+"'"
                num_selectors = 1

        if 'is_admin' in selectors:
            if selectors['is_admin']:
                value = '1'
            else:
                value = '0'
            if num_selectors > 0:
                select_string += " AND is_admin = '"+value+"'"
                num_selectors +=1
            else:
                select_string += " WHERE is_admin = '"+value+"'"
                num_selectors = 1

        if 'is_active' in selectors:
            if selectors['is_active']:
                value = '1'
            else:
                value = '0'
            if num_selectors > 0:
                select_string += " AND is_active = '"+value+"'"
                num_selectors +=1
            else:
                select_string += " WHERE is_active = '"+value+"'"
                num_selectors = 1

        if 'is_locked' in selectors:
            # Staff User account is locked when 'locked_since' is greater or equal than now - ACCOUNT_LOCK_PERIOD_SECONDS
            now_minus_lock_period = datetime.datetime.now() - datetime.timedelta(seconds=app.config['ACCOUNT_LOCK_PERIOD_SECONDS'])
            now_minus_lock_period_str = now_minus_lock_period.isoformat(sep=' ', timespec='seconds')
            if selectors['is_locked']:
                if num_selectors > 0:
                    select_string += " AND locked_since >= '"+now_minus_lock_period_str+"'"
                    num_selectors +=1
                else:
                    select_string += " WHERE locked_since >= '"+now_minus_lock_period_str+"'"
                    num_selectors = 1
            else:
                if num_selectors > 0:
                    select_string += " AND locked_since < '"+now_minus_lock_period_str+"'"
                    num_selectors +=1
                else:
                    select_string += " WHERE locked_since < '"+now_minus_lock_period_str+"'"
                    num_selectors = 1

        object_list = []
        db = get_db()
        for user in db.execute(select_string).fetchall():
            object_list.append(StaffUser(
                    id=user['id'],
                    username=user['username'],
                    password=user['password'],
                    email=user['email'],
                    is_admin=user['is_admin'],
                    is_active=user['is_active'],
                    failed_login_attempts=user['failed_login_attempts'],
                    locked_since=user['locked_since']
            ))
        return object_list

    def query_one(**selectors):
        select_string = "SELECT * FROM user"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'username' in selectors:
            if num_selectors > 0:
                select_string += " AND username = '"+selectors['username']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE username = '"+selectors['username']+"'"
                num_selectors = 1

        if 'password' in selectors:
            if num_selectors > 0:
                select_string += " AND password = '"+selectors['password']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE password = '"+selectors['password']+"'"
                num_selectors = 1

        if 'email' in selectors:
            if num_selectors > 0:
                select_string += " AND email = '"+selectors['email']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE email = '"+selectors['email']+"'"
                num_selectors = 1

        if 'is_admin' in selectors:
            if selectors['is_admin']:
                value = '1'
            else:
                value = '0'
            if num_selectors > 0:
                select_string += " AND is_admin = '"+value+"'"
                num_selectors +=1
            else:
                select_string += " WHERE is_admin = '"+value+"'"
                num_selectors = 1

        if 'is_active' in selectors:
            if selectors['is_active']:
                value = '1'
            else:
                value = '0'
            if num_selectors > 0:
                select_string += " AND is_active = '"+value+"'"
                num_selectors +=1
            else:
                select_string += " WHERE is_active = '"+value+"'"
                num_selectors = 1

        if 'is_locked' in selectors:
            # Staff User account is locked when 'locked_since' is greater or equal than now - ACCOUNT_LOCK_PERIOD_SECONDS
            now_minus_lock_period = datetime.datetime.now() - datetime.timedelta(seconds=app.config['ACCOUNT_LOCK_PERIOD_SECONDS'])
            now_minus_lock_period_str = now_minus_lock_period.isoformat(sep=' ', timespec='seconds')
            if selectors['is_locked']:
                if num_selectors > 0:
                    select_string += " AND locked_since >= '"+now_minus_lock_period_str+"'"
                    num_selectors +=1
                else:
                    select_string += " WHERE locked_since >= '"+now_minus_lock_period_str+"'"
                    num_selectors = 1
            else:
                if num_selectors > 0:
                    select_string += " AND locked_since < '"+now_minus_lock_period_str+"'"
                    num_selectors +=1
                else:
                    select_string += " WHERE locked_since < '"+now_minus_lock_period_str+"'"
                    num_selectors = 1

        object = None
        db = get_db()
        user = db.execute(select_string).fetchone()
        if user:
            object = StaffUser(
                    id=user['id'],
                    username=user['username'],
                    password=user['password'],
                    email=user['email'],
                    is_admin=user['is_admin'],
                    is_active=user['is_active'],
                    failed_login_attempts=user['failed_login_attempts'],
                    locked_since=user['locked_since']
            )
        return object

    def __str__(self):
        return('id='+str(self.id)+', username='+self.username+', email='+self.email+', is_admin='+str(self.is_admin)+', is_active='+str(self.is_active)+', failed_login_attempts='+str(self.failed_login_attempts)+', locked_since='+locked_since)

class MenuItem:

    id = 0

    COFFEE = "Coffee"
    TEA = "Tea"
    COLD_DRINK = "Cold drink"
    DESSERT = "Dessert"

    CATEGORIES = [COFFEE, TEA, COLD_DRINK, DESSERT]

    def __init__(self, item, id=0, category=COFFEE, price="0.0"):

        assert category in self.CATEGORIES
        assert float(price) >= 0.0
        assert float(price) <= 99.99 # 'price' is of SQL type DECIMAL(4,2) - a Float number with max 4 total digits and 2 after decimal dot

        self.id = id
        self.item = item
        self.category = category
        self.price = price # String representation of decimal(4,2) number

    def read(self):
        db = get_db()
        db_row = db.execute(
            'SELECT * FROM menu WHERE item = ?', (self.item,)
        ).fetchone()
        if db_row is None:
            self.id = None
            return None
        else:
            self.id = db_row['id']
            self.category = db_row['category']
            self.price = '{:.2f}'.format(db_row['price'])
            return self

    def save(self):
        save_category = self.category
        save_price = self.price

        assert self.category in self.CATEGORIES
        assert float(self.price) >= 0.0
        assert float(self.price) <= 99.99 # 'price' is of SQL type DECIMAL(4,2) - a Float number with max 4 total digits and 2 after decimal dot

        db = get_db()
        db_row = db.execute(
            'SELECT * FROM menu WHERE item = ?', (self.item,)
        ).fetchone()
        if db_row is None:
            db.execute(
                'INSERT INTO menu (item, category, price) VALUES (?, ?, ?)',
                (self.item, self.category, self.price)
            )
        else:
            db.execute(
                'UPDATE menu SET category = ?, price = ? WHERE item = ?',
                (self.category, self.price, self.item)
            )
        db.commit()

        if self.read():
            if self.category != save_category :
                return False
            elif self.price != save_price :
                return False
            else:
                return True
        else:
            return False

    def delete(self):
        if self.id:
            db = get_db()
            db.execute(
                'DELETE FROM menu WHERE id = ?', (self.id,)
            )
            db.commit()

        if self.read():
            return False
        else:
            return True

    def query_all(**selectors):
        select_string = "SELECT * FROM menu"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'item' in selectors:
            if num_selectors > 0:
                select_string += " AND item = '"+selectors['item']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE item = '"+selectors['item']+"'"
                num_selectors = 1

        if 'category' in selectors:
            if num_selectors > 0:
                select_string += " AND category = '"+selectors['category']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE category = '"+selectors['category']+"'"
                num_selectors = 1

        if 'price' in selectors:
            if num_selectors > 0:
                select_string += " AND price = '"+selectors['price']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE price = '"+selectors['price']+"'"
                num_selectors = 1

        object_list = []
        db = get_db()
        for menu_item in db.execute(select_string).fetchall():
            object_list.append(MenuItem(
                    id=menu_item['id'],
                    item=menu_item['item'],
                    category=menu_item['category'],
                    price='{:.2f}'.format(menu_item['price'])
            ))
        return object_list

    def query_one(**selectors):
        select_string = "SELECT * FROM menu"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'item' in selectors:
            if num_selectors > 0:
                select_string += " AND item = '"+selectors['item']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE item = '"+selectors['item']+"'"
                num_selectors = 1

        if 'category' in selectors:
            if num_selectors > 0:
                select_string += " AND category = '"+selectors['category']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE category = '"+selectors['category']+"'"
                num_selectors = 1

        if 'price' in selectors:
            if num_selectors > 0:
                select_string += " AND price = '"+selectors['price']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE price = '"+selectors['price']+"'"
                num_selectors = 1

        object = None
        db = get_db()
        menu_item = db.execute(select_string).fetchone()
        if menu_item:
            object = MenuItem(
                    id=menu_item['id'],
                    item=menu_item['item'],
                    category=menu_item['category'],
                    price='{:.2f}'.format(menu_item['price'])
            )
        return object

    def __str__(self):
        return('id='+str(self.id)+', item='+self.item+', category='+self.category+', price='+self.price)

class StarPointsCustomer:

    id = 0

    def __init__(self, nick, id=0, name="", email="", points=0, cumulative=0):

        assert int(points) >= 0 # 'points' must be non-negative Integer

        self.id = id
        self.nick = nick
        self.name = name
        self.email = email
        self.points = points
        self.cumulative = cumulative

    def read(self):
        db = get_db()
        db_row = db.execute(
            'SELECT * FROM starpointscustomer WHERE nick = ?', (self.nick,)
        ).fetchone()
        if db_row is None:
            self.id = None
            return None
        else:
            self.id = db_row['id']
            self.name = db_row['name']
            self.email = db_row['email']
            self.points = int(db_row['points'])
            self.cumulative = int(db_row['cumulative'])
            return self

    def save(self):
        save_name = self.name
        save_email = self.email
        save_points = self.points
        save_cumulative = self.cumulative

        assert self.points >= 0 # 'points' must be non-negative Integer

        db = get_db()
        if self.id > 0:
            db_row = db.execute(
                'SELECT * FROM starpointscustomer WHERE id = ?', (self.id,)
            ).fetchone()
        else:
            db_row = None

        if db_row is None:
            db.execute(
                'INSERT INTO starpointscustomer (nick, name, email, points, cumulative) VALUES (?, ?, ?, ?, ?)',
                (self.nick, self.name, self.email, self.points, self.cumulative)
            )
        else:
            db.execute(
                'UPDATE starpointscustomer SET nick = ?, name = ?, email = ?, points = ?, cumulative = ? WHERE id = ?',
                (self.nick, self.name, self.email, self.points, self.cumulative, self.id)
            )
        db.commit()

        if self.read() != None:
            if self.name != save_name :
                return False
            elif self.email != save_email :
                return False
            elif self.points != save_points :
                return False
            elif self.cumulative != save_cumulative:
                return False
            else:
                return True
        else:
            return False

    def delete(self):
        if self.id:
            db = get_db()
            db.execute(
                'DELETE FROM starpointscustomer WHERE id = ?', (self.id,)
            )
            db.commit()

        if self.read():
            return False
        else:
            return True

    def query_all(**selectors):
        select_string = "SELECT * FROM starpointscustomer"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'nick' in selectors:
            if num_selectors > 0:
                select_string += " AND nick = '"+selectors['nick']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE nick = '"+selectors['nick']+"'"
                num_selectors = 1

        if 'name' in selectors:
            if num_selectors > 0:
                select_string += " AND name = '"+selectors['name']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE name = '"+selectors['name']+"'"
                num_selectors = 1

        if 'email' in selectors:
            if num_selectors > 0:
                select_string += " AND email = '"+selectors['email']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE email = '"+selectors['email']+"'"
                num_selectors = 1

        if 'points' in selectors:
            if num_selectors > 0:
                select_string += " AND points = '"+selectors['points']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points = '"+selectors['points']+"'"
                num_selectors = 1

        object_list = []
        db = get_db()
        for sp_customer in db.execute(select_string).fetchall():
            object_list.append(StarPointsCustomer(
                    id=sp_customer['id'],
                    nick=sp_customer['nick'],
                    name=sp_customer['name'],
                    email=sp_customer['email'],
                    points=sp_customer['points'],
                    cumulative=sp_customer['cumulative']
            ))
        return object_list

    def query_one(**selectors):
        select_string = "SELECT * FROM starpointscustomer"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'nick' in selectors:
            if num_selectors > 0:
                select_string += " AND nick = '"+selectors['nick']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE nick = '"+selectors['nick']+"'"
                num_selectors = 1

        if 'name' in selectors:
            if num_selectors > 0:
                select_string += " AND name = '"+selectors['name']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE name = '"+selectors['name']+"'"
                num_selectors = 1

        if 'email' in selectors:
            if num_selectors > 0:
                select_string += " AND email = '"+selectors['email']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE email = '"+selectors['email']+"'"
                num_selectors = 1

        if 'points' in selectors:
            if num_selectors > 0:
                select_string += " AND points = '"+selectors['points']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points = '"+selectors['points']+"'"
                num_selectors = 1

        object = None
        db = get_db()
        sp_customer = db.execute(select_string).fetchone()
        if sp_customer:
            object = StarPointsCustomer(
                    id=sp_customer['id'],
                    nick=sp_customer['nick'],
                    name=sp_customer['name'],
                    email=sp_customer['email'],
                    points=sp_customer['points'],
                    cumulative=sp_customer['cumulative']
            )
        return object

    def __str__(self):
        return('id='+str(self.id)+', nick='+self.nick+', name='+self.name+', email='+self.email+', points='+str(self.points)+', cumulative='+str(self.cumulative))

class RegularOrder:

    id =0

    def __init__(self, total, order_json, cashier_id, id=0, points=0, customer_id=0, order_date=''):

        assert id >=0 , "RegularOrder.id must be non-negative, but is {}".format(id)
        assert total >= 0.0 , "RegularOrder.total must be a non-negative Float, but is '{}'".format(total)
        assert points >= 0 , "RegularOrder.points must be non-negative Integer, but is '{}'".format(points)
        assert cashier_id > 0 , "RegularOrder.cashier_id must be greater than zero, but is '{}'".format(cashier_id)
        assert StaffUser.query_one(id=cashier_id) is not None , "RegularOrder.cashier_id must refer to active Staff user! cashier_id='{}'".format(cashier_id)
        if customer_id > 0:
            assert StarPointsCustomer.query_one(id=customer_id) is not None , "RegularOrder.customer_id must refer to valid Star Points Customer, customer_id='{}'".format(customer_id)
        assert len(order_json)>0 , "RegularOrder.order_json cannot be empty!"

        self.id = id
        self.total = total
        self.cashier_id = cashier_id
        self.order_json = order_json
        self.customer_id = customer_id
        self.points = points
        if order_date == '':
            self.order_date = datetime.datetime.now()
        else:
            self.order_date = order_date

    def save(self):

        assert self.total >= 0.0 , "RegularOrder.total must be a non-negative Float, but is '{}'".format(total)
        assert self.points >= 0 , "RegularOrder.points must be non-negative Integer, but is '{}'".format(points)
        assert self.cashier_id > 0 , "RegularOrder.cashier_id must be greater than zero, but is '{}'".format(cashier_id)
        assert StaffUser.query_one(id=self.cashier_id) is not None , "RegularOrder.cashier_id must refer to active Staff user! cashier_id='{}'".format(cashier_id)
        if self.customer_id > 0:
            assert StarPointsCustomer.query_one(id=self.customer_id) is not None , "RegularOrder.customer_id must refer to valid Star Points Customer, customer_id='{}'".format(customer_id)
        assert len(self.order_json)>0 , "RegularOrder.order_json cannot be empty!"

        db = get_db()
        db_row = None

        if self.id > 0:
            db_row = db.execute(
                'SELECT * FROM regularorder WHERE id = ?', (self.id,)
            ).fetchone()

        if db_row is None:
            db.execute(
                'INSERT INTO regularorder (order_date, total, cashier_id, customer_id, points, order_json) VALUES (?, ?, ?, ?, ?, ?)',
                (self.order_date, self.total, self.cashier_id, self.customer_id, self.points, self.order_json)
            )
            db.commit()
            return True
        else:
            # order with this 'id' already exists, update is not supported!
            return False

    def query_all(**selectors):
        select_string = "SELECT * FROM regularorder"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'date_le' in selectors:
            if num_selectors > 0:
                select_string += " AND order_date <= '"+selectors['date_le']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE order_date <= '"+selectors['date_le']+"'"
                num_selectors = 1

        if 'date_ge' in selectors:
            if num_selectors > 0:
                select_string += " AND order_date >= '"+selectors['date_ge']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE order_date >= '"+selectors['date_ge']+"'"
                num_selectors = 1

        if 'total_le' in selectors:
            if num_selectors > 0:
                select_string += " AND total <= '"+selectors['total_le']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE total <= '"+selectors['total_le']+"'"
                num_selectors = 1

        if 'total_ge' in selectors:
            if num_selectors > 0:
                select_string += " AND total >= '"+selectors['total_ge']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE total >= '"+selectors['total_ge']+"'"
                num_selectors = 1

        if 'cashier_id' in selectors:
            if num_selectors > 0:
                select_string += " AND cashier_id = '"+selectors['cashier_id']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE cashier_id = '"+selectors['cashier_id']+"'"
                num_selectors = 1

        if 'customer_id' in selectors:
            if num_selectors > 0:
                select_string += " AND customer_id = '"+selectors['customer_id']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE customer_id = '"+selectors['customer_id']+"'"
                num_selectors = 1

        if 'points_le' in selectors:
            if num_selectors > 0:
                select_string += " AND points <= '"+selectors['points_le']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points <= '"+selectors['points_le']+"'"
                num_selectors = 1

        if 'points_ge' in selectors:
            if num_selectors > 0:
                select_string += " AND points >= '"+selectors['points_ge']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points >= '"+selectors['points_ge']+"'"
                num_selectors = 1

        object_list = []
        db = get_db()
        for order in db.execute(select_string).fetchall():
            object_list.append(RegularOrder(
                    id=order['id'],
                    total=order['total'],
                    cashier_id=order['cashier_id'],
                    customer_id=order['customer_id'],
                    points=order['points'],
                    order_json=order['order_json'],
                    order_date=order['order_date']
            ))
        return object_list

    def __str__(self):
        return('id='+str(self.id)+', total='+str(self.total)+", order_date="+str(self.order_date)+', cashier_id='+str(self.cashier_id)+', customer_id='+str(self.customer_id)+', points='+str(self.points)+', order_json'+self.order_json)

class StarPointsOrder:

    id =0

    def __init__(self, points, order_json, cashier_id, customer_id, id=0, created=''):

        assert id >=0 , "StarPointsOrder.id must be non-negative, but is {}".format(id)
        assert points >= 0 , "StarPointsOrder.points must be non-negative Integer, but is '{}'".format(points)
        assert cashier_id > 0 , "StarPointsOrder.cashier_id must be greater than zero, but is '{}'".format(cashier_id)
        assert StaffUser.query_one(id=cashier_id) is not None , "StarPointsOrder.cashier_id must refer to active Staff user! cashier_id='{}'".format(cashier_id)
        assert customer_id > 0 , "StarPointsOrder.customer_id must be greater than zero, but is '{}'".format(customer_id)
        assert StarPointsCustomer.query_one(id=customer_id) is not None , "StarPointsOrder.customer_id must refer to valid Star Points Customer, customer_id='{}'".format(customer_id)
        assert len(order_json)>0 , "StarPointsOrder.order_json cannot be empty!"

        self.id = id
        self.cashier_id = cashier_id
        self.order_json = order_json
        self.customer_id = customer_id
        self.points = points
        if created == '':
            self.created = datetime.datetime.now()
        else:
            self.created = created

    def save(self):

        assert self.id >=0 , "StarPointsOrder.id must be non-negative, but is {}".format(id)
        assert self.points >= 0 , "StarPointsOrder.points must be non-negative Integer, but is '{}'".format(points)
        assert self.cashier_id > 0 , "StarPointsOrder.cashier_id must be greater than zero, but is '{}'".format(cashier_id)
        assert StaffUser.query_one(id=self.cashier_id) is not None , "StarPointsOrder.cashier_id must refer to active Staff user! cashier_id='{}'".format(cashier_id)
        assert self.customer_id > 0 , "StarPointsOrder.customer_id must be greater than zero, but is '{}'".format(customer_id)
        assert StarPointsCustomer.query_one(id=self.customer_id) is not None , "StarPointsOrder.customer_id must refer to valid Star Points Customer, customer_id='{}'".format(customer_id)
        assert len(self.order_json)>0 , "StarPointsOrder.order_json cannot be empty!"

        db = get_db()
        db_row = None

        if self.id > 0:
            db_row = db.execute(
                'SELECT * FROM starpointsorder WHERE id = ?', (self.id,)
            ).fetchone()

        if db_row is None:
            db.execute(
                'INSERT INTO starpointsorder (created, points, cashier_id, customer_id, order_json) VALUES (?, ?, ?, ?, ?)',
                (self.created, self.points, self.cashier_id, self.customer_id, self.order_json)
            )
            db.commit()
            return True
        else:
            # order with this 'id' already exists, update is not supported!
            return False

    def query_all(**selectors):
        select_string = "SELECT * FROM starpointsorder"
        num_selectors = 0

        if 'id' in selectors:
            select_string += " WHERE id = '"+str(selectors['id'])+"'"
            num_selectors = 1

        if 'date_le' in selectors:
            if num_selectors > 0:
                select_string += " AND created <= '"+selectors['date_le']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE created <= '"+selectors['date_le']+"'"
                num_selectors = 1

        if 'date_ge' in selectors:
            if num_selectors > 0:
                select_string += " AND created >= '"+selectors['date_ge']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE created >= '"+selectors['date_ge']+"'"
                num_selectors = 1

        if 'cashier_id' in selectors:
            if num_selectors > 0:
                select_string += " AND cashier_id = '"+selectors['cashier_id']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE cashier_id = '"+selectors['cashier_id']+"'"
                num_selectors = 1

        if 'customer_id' in selectors:
            if num_selectors > 0:
                select_string += " AND customer_id = '"+selectors['customer_id']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE customer_id = '"+selectors['customer_id']+"'"
                num_selectors = 1

        if 'points_le' in selectors:
            if num_selectors > 0:
                select_string += " AND points <= '"+selectors['points_le']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points <= '"+selectors['points_le']+"'"
                num_selectors = 1

        if 'points_ge' in selectors:
            if num_selectors > 0:
                select_string += " AND points >= '"+selectors['points_ge']+"'"
                num_selectors +=1
            else:
                select_string += " WHERE points >= '"+selectors['points_ge']+"'"
                num_selectors = 1

        object_list = []
        db = get_db()
        for order in db.execute(select_string).fetchall():
            object_list.append(StarPointsOrder(
                    id=order['id'],
                    cashier_id=order['cashier_id'],
                    customer_id=order['customer_id'],
                    points=order['points'],
                    order_json=order['order_json'],
                    created=order['created']
            ))
        return object_list

    def __str__(self):
        return('id='+str(self.id)+", created="+str(self.created)+', cashier_id='+str(self.cashier_id)+', customer_id='+str(self.customer_id)+', points='+str(self.points)+', order_json'+self.order_json)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('PyCafe database initalized and empty.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
