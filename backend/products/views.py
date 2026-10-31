from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.permissions import staff_required
from products.models import Product, ProductVariant, Plan, TaxRule, Discount
from products.forms import ProductForm, ProductVariantForm, PlanForm, TaxRuleForm, DiscountForm


@staff_required
def products_list_view(request):
    products = Product.objects.prefetch_related('variants').all()
    form = ProductForm()
    variant_form = ProductVariantForm()

    if request.method == 'POST':
        if 'create_product' in request.POST:
            form = ProductForm(request.POST)
            if form.is_valid():
                p = form.save()
                messages.success(request, f"Product '{p.name}' created.")
                return redirect('products')
        elif 'create_variant' in request.POST:
            variant_form = ProductVariantForm(request.POST)
            if variant_form.is_valid():
                v = variant_form.save()
                messages.success(request, f"Variant '{v.name}' added to {v.product.name}.")
                return redirect('products')

    return render(request, 'products/product_list.html', {
        'products': products,
        'form': form,
        'variant_form': variant_form,
    })


@staff_required
def plans_list_view(request):
    plans = Plan.objects.all()
    form = PlanForm()

    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            pl = form.save()
            messages.success(request, f"Plan '{pl.name}' created.")
            return redirect('plans')

    return render(request, 'products/plan_list.html', {
        'plans': plans,
        'form': form,
    })


@staff_required
def rules_list_view(request):
    taxes = TaxRule.objects.all()
    discounts = Discount.objects.all()
    tax_form = TaxRuleForm()
    discount_form = DiscountForm()

    if request.method == 'POST':
        if 'create_tax' in request.POST:
            tax_form = TaxRuleForm(request.POST)
            if tax_form.is_valid():
                t = tax_form.save()
                messages.success(request, f"Tax rule '{t.name}' created.")
                return redirect('rules_list')
        elif 'create_discount' in request.POST:
            discount_form = DiscountForm(request.POST)
            if discount_form.is_valid():
                d = discount_form.save()
                messages.success(request, f"Discount rule '{d.name}' created.")
                return redirect('rules_list')

    return render(request, 'products/rules_list.html', {
        'taxes': taxes,
        'discounts': discounts,
        'tax_form': tax_form,
        'discount_form': discount_form,
    })
