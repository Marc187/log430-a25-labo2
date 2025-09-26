"""
Orders (read-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

from db import get_sqlalchemy_session, get_redis_conn
from sqlalchemy import desc
from models.order import Order
from models.order_item import OrderItem
from collections import defaultdict
from models.product import Product
from queries.read_product import get_product_by_id
from queries.read_user import get_user_by_id

def get_order_by_id(order_id):
    """Get order by ID from Redis"""
    r = get_redis_conn()
    return r.hgetall(order_id)

def get_orders_from_mysql(limit=9999):
    """Get last X orders"""
    session = get_sqlalchemy_session()
    return session.query(Order).order_by(desc(Order.id)).limit(limit).all()

def get_orders_from_redis(limit=9999):
    """Get last X orders"""
    # TODO: écrivez la méthode
    r = get_redis_conn()
    keys = [k for k in r.keys("order:*") if not k.endswith(":items")]
    keys = sorted(keys, key=lambda k: int(k.split(":")[1]), reverse=True)[:limit]

    orders = []
    for key in keys:
        order_data = r.hgetall(key)
        item_keys = r.smembers(f"{key}:items")

        order = Order(id=int(order_data["id"]),
                      user_id=int(order_data["user_id"]),
                      total_amount=float(order_data["total_amount"]))

        for item_key in item_keys:
            item_data = r.hgetall(item_key)

            order_item = OrderItem(order_id=int(item_data["order_id"]),
                                   product_id=int(item_data["product_id"]),
                                   quantity=int(item_data["quantity"]),
                                   unit_price=float(item_data["unit_price"]))
            order.order_items.append(order_item)

        orders.append(order)

    return orders

def get_highest_spending_users():
    """Get report of best selling products"""
    # TODO: écrivez la méthode
    # triez le résultat par nombre de commandes (ordre décroissant)
    orders = get_orders_from_redis()

    expenses_by_user = defaultdict(float)

    for order in orders:
        expenses_by_user[order.user_id] += order.total_amount

    highest_spending_users = sorted(expenses_by_user.items(), key=lambda item: item[1], reverse=True)

    result = []
    for user_id, total_spent in highest_spending_users[:10]:
        user = get_user_by_id(user_id)
        result.append({ "name": user["name"], "total_spent": total_spent })

    return result

def get_top_selling_products():
    r = get_redis_conn()
    products = defaultdict(int)
    keys = r.keys("product:*")

    for key in keys:
        product_id = int(key.split(":")[1])
        product_count = int(r.get(key))
        products[product_id] = product_count

    top_product_ids = sorted(products.items(), key=lambda x: x[1], reverse=True)[:10]
    top_products = []
    for product_id, _ in top_product_ids:
        product = get_product_by_id(product_id)
        top_products.append({ "name": product["name"], "quantity_sold": products[product_id]})

    return top_products