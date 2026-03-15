def delete_inventory_by_vin(db, vin):
    db.execute("DELETE FROM inventory WHERE vin_number = %s;", (vin,))

def delete_sales_by_vin(db, vin):
    db.execute("DELETE FROM sales WHERE vin_number = %s;", (vin,))

def insert_inventory_record(db, vin, make, model, year, mileage, condition_type, cost, sale_price, profit_percent, status, location):
    query = '''
    INSERT INTO inventory
    (vin_number, make, model, year, mileage, condition_type, cost, sale_price, profit_percent, status, location)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    '''
    db.execute(query, (vin, make, model, year, mileage, condition_type, cost, sale_price, profit_percent, status, location))

def insert_sales_record(db, sale_id, vin, sale_price, payment_method, deposit, loan_term, loan_interest, monthly_payment, status):
    query = '''
    INSERT INTO sales
    (sale_id, vin_number, sale_price, payment_method, deposit, loan_term, loan_interest, monthly_payment, status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
    '''
    db.execute(query, (sale_id, vin, sale_price, payment_method, deposit, loan_term, loan_interest, monthly_payment, status))
