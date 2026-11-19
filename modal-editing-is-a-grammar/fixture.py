def total_price(items, tax_rate):
    subtotal = sum(item.price for item in items)
    discount = apply_discount(subtotal, "SPRING-SALE")
    return round(subtotal * (1 + tax_rate) - discount, 2)

def legacy_helper():
    pass
