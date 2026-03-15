GET_SALE_BY_VIN = '''
SELECT sale_id, vin_number, sale_price, payment_method, deposit, loan_term,
       loan_interest, monthly_payment, status
FROM sales
WHERE vin_number = %s;
'''
