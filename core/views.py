from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from core.forms import ProductForm, CheckoutForm
from django.contrib import messages
from core.models import Product, Order, OrderItem, CheckoutAddress
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django.views.generic import ListView
# from django_xhtml2pdf.utils import generate_pdf
import os
from django.contrib.staticfiles import finders
# from xhtml2pdf import pisa

import razorpay

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))


# Create your views here.
# context_object_name = 'product'


def index(request):
    products = Product.objects.all()
    return render(request, 'core/index.html', {'products': products})


class ProductListview(ListView):
    model = Product
    template_name = 'core/index.html'
    context_object_name = 'events'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProductListview, self).get_context_data()
        context['REDIS_CASHED_TIME'] = settings.REDIS_CASHED_TIME
        return context


def add_product(request):
    if request.method == "POST":
        print(request.FILES)
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Product Add Successfully')
            return redirect('/')
        else:
            messages.info(request, "Product not added")
    else:
        form = ProductForm()
    return render(request, 'core/add_product.html', {'form': form})


def product_dec(request, pk):
    product = Product.objects.get(pk=pk)
    return render(request, 'core/product_desc.html', {'product': product})


def add_to_card(request, pk):
    product = Product.objects.get(pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'Added Quantity Item')
            return redirect("product_desc", pk=pk)
        else:
            order.items.add(order_item)
            messages.info(request, "Items add to Card")
            return redirect("product_desc", pk=pk)

    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, order_date=order_date)
        order.items.add(order_item)
        messages.info(request, "Items add to Card")
        return redirect("product_desc", pk=pk)


def orderlist(request):
    if Order.objects.filter(user=request.user, ordered=False).exists():
        order = Order.objects.get(user=request.user, ordered=False)

        return render(request, 'core/orderlist.html', {'order': order})
    messages.info(request, 'llllll')
    return render(request, 'core/orderlist.html', {'messages': "your card is empty"})


def add_item(request, pk):
    product = Product.objects.get(pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            if order_item.quantity < product.product_available_count:
                order_item.quantity += 1
                order_item.save()
                messages.info(request, 'Added Quantity Item')
                return redirect("orderlist")
            else:
                messages.info(request, "product is out of stock")
                return redirect("orderlist")
        else:
            order.items.add(order_item)
            messages.info(request, "Items add to Card")
            return redirect("product_desc", pk=pk)

    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, order_date=order_date)
        order.items.add(order_item)
        messages.info(request, "Items add to Card")
        return redirect("product_desc", pk=pk)


def remove_item(request, pk):
    item = get_object_or_404(Product, pk=pk)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item = OrderItem.objects.filter(
                product=item,
                user=request.user,
                ordered=False,
            )[0]

            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Item Quantity Update")
            return redirect("orderlist")
        else:
            messages.info(request, "item is not in your cart")
            return redirect("orderlist")
    else:
        messages.info(request, "you dont have any order")
        return redirect('orderlist')


def checkout_page(request):
    if CheckoutAddress.objects.filter(user=request.user).exists():
        # messages.info(request, 'uuuuuuu')

        return render(request, 'core/checkout_address.html', {'payment_allow': 'allow'})
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        try:
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip')

                checkout_adress = CheckoutAddress(
                    user=request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip_code=zip
                )
                checkout_adress.save()
                messages.info(request, 'it shoud render summery page')

                return render(request, 'core/checkout_address.html', {'payment_allow': "allow"})


        except ObjectDoesNotExist:
            messages.WARNING(request, 'failed check out')
            return redirect('checkout_page')
    else:
        form = CheckoutForm()
        # payment(request)
        # messages.info(request,'yyyyyyyyyyy')
        return render(request, 'core/checkout_address.html', {'form': form})


def payment(request):
    try:
        order = Order.objects.get(user=request.user, ordered=False)
        address = CheckoutAddress.objects.get(user=request.user)
        order_amount = order.get_total_price()
        order_currency = "INR"
        order_receipt = order.order_id
        notes = {
            "street_address": address.street_address,
            "apartment_address": address.apartment_address,
            "country": address.country.name,
            "zip_code": address.zip_code,
        }
        razorpay_order = razorpay_client.order.create(
            dict(
                amount=order_amount * 100,
                currency=order_currency,
                receipt=order_receipt,
                notes=notes,
                payment_capture="0"

            )
        )
        print(razorpay_order["id"])
        order.razorpay_order_id = razorpay_order["id"]
        order.save()
        print('it render summery page')
        return render(request, "core/paymentsumaryrazorpay.html", {
            "order": order,
            "order_id": razorpay_order["id"],
            "orderid": order.order_id,
            "final_price": order_amount,
            "razorpay_merchant_id": settings.RAZORPAY_ID,

        })
    except ObjectDoesNotExist:
        print("dos not exist")
        return HttpResponse("404 error")


@csrf_exempt
def handlerequest(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            print(order_id, payment_id, signature)
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,

            }
            try:
                order_db = Order.objects.get(razorpay_order_id=order_id)
                print('order found')
            except:
                print('order did not found')
                return HttpResponse('505 not found')
            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()
            print('workiiing')
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            if result == None:
                print('it working')
                amount = order_db.get_total_price()
                amount = amount * 100
                payment_status = razorpay_client.payment.capture(payment_id, amount)
                if payment_status is not None:
                    print(payment_status)
                    order_db.ordered = True
                    order_db.save()
                    print('payment success')
                    checkout_address = CheckoutAddress.objects.get(user=request.user)
                    request.session[
                        "order completed"] = "your order successfuly placed"
                    request.session["order_id"] = order_id
                    request.session["payment_status"] = payment_status
                    return render(request, "core/invoice.html", {'order': order_db,
                                                                 "payment_status": payment_status,
                                                                 "checkout_address": checkout_address})
                else:
                    print('payment faild')
                    order_db.ordered = False
                    order_db.save()
                    request.session["order failed"] = "your order could not payed"
                    return redirect('/')
            else:
                order_db.ordered = False
                order_db.save()
                return render(request, "core/paymentfaild.html")
        except:
            return HttpResponse("Error Occurred")


def invoice(request):
    return render(request, 'core/invoice.html')


def render_pdf_view(request):
    order_id = request.session["order_id"]
    order_db = Order.objects.get(razorpay_order_id=order_id)
    checkout_address = CheckoutAddress.objects.filter(user=request.user)
    amount = order_db.get_total_price()
    amount = amount * 100
    payment_id = order_db.razorpay_payment_id
    payment_status = razorpay_client.payment.capture(payment_id, amount)
    template_path = 'core/invoice.html'
    context = {
        "order": order_db, "payment_status": payment_status, "checkout_address": checkout_address
    }
    responce = HttpResponse(content_type='application/pdf')
    responce['content-disposition'] = 'attachment; filename="report.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    #  pisa_status = generate_pdf.CreatPDF(
    #     html, dest=responce
    # )
    #  if pisa_status.err:
    #     return HttpResponse('we have some error' + html)
    return responce
