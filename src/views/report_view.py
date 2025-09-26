"""
Report view
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from queries.read_order import get_highest_spending_users, get_top_selling_products
from views.template_view import get_template, get_param

def show_highest_spending_users():
    """ Show report of highest spending users """
    users = get_highest_spending_users()
    rows = [f"""
            <tr>
                <td>{user["name"]}</td>
                <td>{user["total_spent"]}</td>
            </tr> """ for user in users]

    return get_template(f"""
                        <h2>Les plus gros acheteurs</h2>
                        <p>
                            <table class="table">
                                <tr>
                                    <th>Nom</th>
                                    <th>Total Dépensé</th>
                                </tr>
                                {" ".join(rows)}
                            </table>
                        </p>""")

def show_best_sellers():
    """ Show report of best selling products """
    products = get_top_selling_products()
    rows = [f"""
            <tr>
                <td>{product["name"]}</td>
                <td>{product["quantity_sold"]}</td>
            </tr> """ for product in products]

    return get_template(f"""
                        <h2>Les articles les plus vendus</h2>
                        <p>
                            <table class="table">
                                <tr>
                                    <th>Nom</th>
                                    <th>Total Dépensé</th>
                                </tr>
                                {" ".join(rows)}
                            </table>
                        </p>""")