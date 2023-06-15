from django.contrib import admin
from .models import Customer, Category, Product, Order, OrderItem, CheckoutAddress

# Register your models here.
admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CheckoutAddress)
