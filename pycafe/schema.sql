DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS menu;
DROP TABLE IF EXISTS regularorder;
DROP TABLE IF EXISTS starpointscustomer;
DROP TABLE IF EXISTS starpointsorder;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  is_admin BOOLEAN,
  is_active BOOLEAN,
  failed_login_attempts INTEGER,
  locked_since DATETIME
);

CREATE TABLE menu (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item VARCHAR(30) UNIQUE NOT NULL,
  category VARCHAR(20) NOT NULL,
  price DECIMAL(4,2)
);

CREATE TABLE regularorder (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  total DECIMAL(5,2),
  points INTEGER NOT NULL CHECK (points >= 0),
  customer_id INTEGER NOT NULL,
  cashier_id INTEGER NOT NULL,
  order_json TEXT NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES starpointscustomer (id),
  FOREIGN KEY (cashier_id) REFERENCES user (id)
);

CREATE TABLE starpointscustomer (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(255) NOT NULL,
  nick VARCHAR(20) NOT NULL,
  email VARCHAR(100) NOT NULL,
  points INTEGER NOT NULL CHECK (points >= 0),
  cumulative INTEGER NOT NULL
);

CREATE TABLE starpointsorder (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  points INTEGER NOT NULL CHECK (points >= 1),
  customer_id INTEGER NOT NULL,
  cashier_id INTEGER NOT NULL,
  order_json TEXT NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES starpointscustomer (id),
  FOREIGN KEY (cashier_id) REFERENCES user (id)
);
