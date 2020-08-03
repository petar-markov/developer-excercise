from flask import render_template, request, redirect, url_for, flash
from app import app, db
from itertools import chain
from collections import Counter
from app.models import Products, Deals


#
# All of the routes are in a single file, since in total it is less than a few hundred lines of code
# TODO: Split this into single modules, if these are to be extended more.



@app.route("/")
def index():
    #Retrieve all products and deals data
    products = Products.query.all()
    deals_data = Deals.query.all()
    return render_template("index.html", products=products, deals_data=deals_data)


@app.route("/submit", methods=["POST"])
def submit():
    if request.method == "POST":

        #This is for adding the deals with the button in there
        if "submit_for_deal" in request.form:
            deal_type = request.form["deal_type"]
            deal_products = request.form["products_for_deal"]
            current_deal = Deals.query.filter_by(deal_type=deal_type).first()
            if deal_products == "":
                return redirect(url_for("index"))

            if current_deal is not None:
                current_deal.deal_items += f', {deal_products}'
                db.session.commit()
                return redirect(url_for("index"))
            else:
                data = Deals(deal_type, deal_products)
                db.session.add(data)
                db.session.commit()
                return redirect(url_for("index"))
        
        product = request.form["product"]
        price = request.form["price"]
        
        if product == "" and price == "":
            return redirect(url_for("index"))

        #If we do not have the submit_for_deal input then we add product
        #This way we keep both the submits in one single route
        data = Products(product, price)
        db.session.add(data)
        db.session.commit()
        
        return redirect(url_for("index"))


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):

    #Deleting a product, should not have issues with it, but still wrapped with a try-except block
    product_for_delete = Products.query.filter_by(id=product_id).first()
    try:
        db.session.delete(product_for_delete)
        db.session.commit()
        return redirect(url_for("index"))
    except:
        return "Something went wrong with this product deletion, please verify the ID..."


@app.route('/delete_deal/<int:deal_id>')
def delete_deal(deal_id):

    #Deleting a whole deal

    #TODO: a delete of an item/items from a single deal can be implemented.
    #      For this we will probably need some addinitional data, like which deal we target, product/products, etc.
    #      Could be that a new route or script is needed for this one.
    deal_for_delete = Deals.query.filter_by(id=deal_id).first()
    try:
        db.session.delete(deal_for_delete)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return 'Something went wrong with this deal deletion, please verify the ID...'


@app.route("/scan", methods=["POST"])
def scan():
    if request.method == "POST":

        #TODO: This needs to be re-factored and improved, since it does not cover all of the possible
        #      scenarios and limit cases.
        #
        #Building the logic for the 2 deals described
        #We first collect the products and their prices so that we can access them easier later on
        #TODO: Since there was no description about which deal is taking with priority if both apply for a product/set of products we follow the instructions.
        #      This can be tunned so that different scenarios with deals prioritizations are handled.

        items_for_scan = request.form["products_for_scan"].replace('\"', "").split(", ")

        all_products = Products.query.all()
        deals_data = Deals.query.all() 
        all_product_names = [product.name for product in all_products]
        
        #we get the intersection of the products available in our database and what was submitted for scan
        #if there are non-valid items for scan or None/Null passed, we will stop and return the index page
        if len(set(all_product_names) & set(items_for_scan)) == 0:
            return render_template("index.html", products=all_products, deals_data=deals_data, result_message='No valid input for scan...')            
        
        items_buy_1_get_1_half_price = list(chain.from_iterable([deal.deal_items.split(", ") 
                                                    for deal in Deals.query.filter_by(deal_type="buy_1_get_1_half_price").all()]))
        items_2_for_3 = list(chain.from_iterable([deal.deal_items.split(", ") 
                                                    for deal in Deals.query.filter_by(deal_type="2_for_3").all()]))
        
        scanned_items_prices = {x: Products.query.filter_by(name=x).first().price for x in items_for_scan}
        scanned_items_prices = {x: int(scanned_items_prices[x][:-1]) if 'c' in scanned_items_prices[x] \
                                    else int(scanned_items_prices[x]) for x in scanned_items_prices.keys()}
        
        scanned_items_count = dict(Counter(items_for_scan)) # converting to a regular dictionary
        
        prices_2_for_3 = []
        current_prices = []
        
        #In this loop we are basically finalizing the total price that we will output in the result
        for item in items_for_scan:
            current_prices.append(scanned_items_prices[item])

            if item in items_2_for_3:
                prices_2_for_3.append(scanned_items_prices[item])

                #if we have reached the 2 for 3 deal satisfaction criteria -> we distract the cheapest item and remove all elements from the list with prices for the deal
                if len(prices_2_for_3) == 3:
                    current_prices.remove(min(prices_2_for_3))
                    del prices_2_for_3[:]
                
                continue
            else:
                if (item in items_buy_1_get_1_half_price) and (scanned_items_count[item] >= 2):
                    current_prices.remove(scanned_items_prices[item])
                    current_prices.append((scanned_items_prices[item] * 0.5))
                    scanned_items_count[item] -= 2

        #Formating a little the final price as per the requirements
        total_price = int(sum(current_prices))
        if total_price > 100:
            result_message = f'{total_price // 100} aws and {total_price % 100} clouds'
        else:
            result_message = f'{total_price} clouds'
        
        #If for some reason we have empty result message
        if result_message == '':
            result_message = 'Something wen\'t wrong with the calculation.'
      
        return render_template("index.html", products=all_products, deals_data=deals_data, result_message=result_message)