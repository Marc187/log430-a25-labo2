<div align="center">

<center>
<h1 style="font-size:18pt;">
Labo 02 – Architecture monolithique, ORM, CQRS, Persistance polyglotte, DDD
</h1>
</center>

<br>
<br>
<br>
<br>

<center>
<h2 style="font-size:16pt;">
PAR
</h2>
</center>

<br>
<br>

<center>
<h2 style="font-size:16pt;">
Marc CHARLEBOIS, CHAM65260301
</h2>
</center>

<br>
<br>
<br>
<br>
<br>
<br>

<center>
<h3 style="font-size:14pt;">
RAPPORT DE LABORATOIRE PRÉSENTÉ À MONSIEUR FABIO PETRILLO DANS LE CADRE DU COURS <em>ARCHITECTURE LOGICIELLE</em> (LOG430-01)
</h3>
</center>

<br>
<br>
<br>
<br>
<br>

<center>
<h3 style="font-size:14pt;">
MONTRÉAL, LE 26 SEPTEMBRE 2025
</h3>
</center>

<br>
<br>
<br>
<br>
<br>

<center>
<h3 style="font-size:14pt;">
ÉCOLE DE TECHNOLOGIE SUPÉRIEURE<br>
UNIVERSITÉ DU QUÉBEC
</h3>
</center>

<br>
<br>
<br>
<br>
<br>

</div>

---
## **Tables des matières**
- [**Tables des matières**](#tables-des-matières)
  - [**Introduction**](#introduction)
  - [**Question 1**](#question-1)
  - [**Question 2**](#question-2)
  - [**Question 3**](#question-3)
  - [**Question 4**](#question-4)
  - [**Question 5**](#question-5)
  - [**CI/CD**](#cicd)

<br>
<br>
<br>
<br>
<br>

---

<div align="justify">

### **Introduction**

Dans ce laboratoire, on apprend à développer une application monolithique de gestion de magasin en appliquant CQRS, la persistance polyglotte (MySQL/Redis), l’usage d’un ORM et des concepts clés du DDD, afin d’optimiser la gestion et les rapports tout en pratiquant une architecture logicielle complète.


### **Question 1**

> Lorsque l'application démarre, la synchronisation entre Redis et MySQL est-elle initialement déclenchée par quelle méthode ? Veuillez inclure le code pour illustrer votre réponse.

La synchronisation initiale entre MySQL et Redis est déclenchée dès qu’un utilisateur appelle la racine de l’application (`GET /` ou `/home`). La chaîne d’appel est la suivante : dans store_manager.py, la méthode `do_GET()` détecte la requête vers `/` et appelle `show_main_menu()` dans template_view.py. Cette fonction invoque `populate_redis_from_mysql()` dans order_controller.py, qui appelle à son tour `sync_all_orders_to_redis()` dans write_order.py. C’est donc cette dernière fonction qui effectue la synchronisation effective, mais elle est initialement déclenchée par l’appel à `show_main_menu()` via `do_GET()`.

La suite d'appel (callstack) se fait comme-ci:

store_manager.py
```Python
class StoreManager(BaseHTTPRequestHandler):
    def do_GET(self):
        """ Handle GET requests received by the http.server """
        id = self.path.split("/")[-1]
        if self.path == "/" or self.path == "/home":
            self._send_html(show_main_menu())
            return

        ...
```

template_view.py
```Python
def show_main_menu():
    """ Show main menu, populate Redis if needed """
    populate_redis_from_mysql()
    return get_template("""
        <nav>
            <h2>Formulaires d'enregistrement</h2>
            <ul class="list-group">
                <li class="list-group-item"><a href="/users">Utilisateurs</a></li>
                <li class="list-group-item"><a href="/products">Articles</a></li>
                <li class="list-group-item"><a href="/orders">Commandes</a></li>
            </ul>
            <br>
            <h2>Rapports</h2>
            <ul class="list-group">
                <li class="list-group-item"><a href="/orders/reports/highest_spenders">Les plus gros acheteurs</a></li>
                <li class="list-group-item"><a href="/orders/reports/best_sellers">Les articles les plus vendus</a></li>
            </ul>
        </nav>""", homepage=True)
```

order_controller.py
```Python
def populate_redis_from_mysql():
   """Populate Redis with orders from MySQL, only if MySQL is empty"""
   sync_all_orders_to_redis()

```
write_order.py

```Python
def sync_all_orders_to_redis():
    """ Sync orders from MySQL to Redis """
    # redis
    r = get_redis_conn()
    orders_in_redis = r.keys(f"order:*")
    rows_added = 0
    try:
        if len(orders_in_redis) == 0:
            # mysql
            orders_from_mysql = get_orders_from_mysql()

            print(orders_from_mysql)

            for order in orders_from_mysql:
                add_order_to_redis(order.id, order.user_id, order.total_amount, order.order_items)
                rows_added += 1

            rows_added = len(orders_from_mysql)
        else:
            print('Redis already contains orders, no need to sync!')
    except Exception as e:
        print(e)
        return 0
    finally:
        return len(orders_in_redis) + rows_added

```


```Python
def add_order_to_redis(order_id, user_id, total_amount, items):
    """Insert order to Redis"""
    r = get_redis_conn()
    pipe = r.pipeline()

    # Orders
    pipe.hset(f"order:{order_id}", mapping={
        "id": order_id,
        "user_id": user_id,
        "total_amount": total_amount,
    })


    for item in items:
        key = f"order_item:{item.id}"

        # OrderItems
        pipe.hset(key, mapping={
            "order_id": order_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

        # Order item keys
        pipe.sadd(f"order:{order_id}:items", key)

        # Increment product counter
        pipe.incrby(f"product:{item.product_id}", int(item.quantity))

    pipe.execute()
```


### **Question 2**

> Quelles méthodes avez-vous utilisées pour lire des données à partir de Redis ? Veuillez inclure le code pour illustrer votre réponse.

Pour lire les données à partir de Redis, j’ai utilisé principalement `keys`, `hgetall` et `smembers` de l’API Redis. La méthode `keys("order:*")` permet de récupérer toutes les commandes stockées, puis elles sont filtrées et triées. Pour chaque commande, `hgetall(key)` lit les champs de l’objet `order` (id, user_id, total_amount). Ensuite, `smembers(f"{key}:items")` récupère les clés associées aux items de la commande, et `hgetall(item_key)` permet de lire chaque OrderItem.

```Python
def get_orders_from_redis(limit=9999):
    """Get last X orders"""
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
```


### **Question 3**

> Quelles méthodes avez-vous utilisées pour ajouter des données dans Redis ? Veuillez inclure le code pour illustrer votre réponse.

Pour insérer les nouvelles commandes dans Redis, je n’ai pas eu besoin de recréer la logique car j’avais déjà implémenté précédemment la méthode `add_order_to_redis` pour faire la synchronisation des commandes entre MySQL et Redis. Ici, c’est à partir de la fonction `add_order` dans write_order.py que l’appel se fait : une fois la commande et ses items ajoutés et validés dans MySQL, j’ai simplement ajouté l’appel suivant : `add_order_to_redis(order_id, user_id, total_amount, created_items)`

Cette méthode utilise `hset` pour stocker les champs de la commande et des items, `sadd` pour relier les items à la commande, et `incrby` pour incrémenter le compteur de ventes d’un produit. Ainsi, la cohérence avec Redis est automatiquement assurée par `add_order` grâce à l’appel de add_order_to_redis.


```Python
def add_order_to_redis(order_id, user_id, total_amount, items):
    """Insert order to Redis"""
    r = get_redis_conn()
    pipe = r.pipeline()

    # Orders
    pipe.hset(f"order:{order_id}", mapping={
        "id": order_id,
        "user_id": user_id,
        "total_amount": total_amount,
    })


    for item in items:
        key = f"order_item:{item.id}"

        # OrderItems
        pipe.hset(key, mapping={
            "order_id": order_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

        # Order item keys
        pipe.sadd(f"order:{order_id}:items", key)

        # Increment product counter
        pipe.incrby(f"product:{item.product_id}", int(item.quantity))

    pipe.execute()
```


### **Question 4**

> Quelles méthodes avez-vous utilisées pour supprimer des données dans Redis ? Veuillez inclure le code pour illustrer votre réponse.

Pour la suppression côté Redis, j’ai déclenché l’opération depuis `delete_order` après la suppression MySQL en appelant `delete_order_from_redis(order_id)`. Dans cette méthode, j’utilise un pipeline pour regrouper les commandes et garantir une seule exécution, `smembers` pour récupérer toutes les clés d’items associées à la commande, puis `delete` pour supprimer chaque hash d’item ainsi que l’ensemble des liens et la hash de la commande, avant `execute` pour valider le lot :

```Python
def delete_order(order_id: int):
    ...
    if order:
        session.delete(order); session.commit()
        delete_order_from_redis(order_id)  # <- déclenche la suppression Redis

def delete_order_from_redis(order_id):
    """Delete order from Redis"""
    r = get_redis_conn()
    pipe = r.pipeline()

    item_keys = r.smembers(f"order:{order_id}:items")

    for item_key in item_keys:
        pipe.delete(item_key)

    pipe.delete(f"order:{order_id}:items")
    pipe.delete(f"order:{order_id}")

    pipe.execute()
```

### **Question 5**
> Si nous souhaitions créer un rapport similaire, mais présentant les produits les plus vendus, les informations dont nous disposons actuellement dans Redis sont-elles suffisantes, ou devrions-nous chercher dans les tables sur MySQL ? Si nécessaire, quelles informations devrions-nous ajouter à Redis ? Veuillez inclure le code pour illustrer votre réponse.

Oui, les informations présentes dans Redis sont suffisantes pour créer un rapport sur les produits les plus vendus, similaire à `get_highest_spending_users`, sans devoir repasser par MySQL. En effet, lors de l’insertion des commandes, j'ai fait en sorte que chaque `order_item` est déjà stocké dans Redis et le compteur de ventes par produit. Cela permet de calculer facilement le nombre total d’articles vendus par produit et de produire un classement similaire à celui des plus gros acheteurs, même sans avoir à implémenter la structure donnée dans la question suivante: `r.incr("product:123", 1)`

```Python
def get_highest_spending_users():
    """Get report of best selling products"""
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
```

### **CI/CD**