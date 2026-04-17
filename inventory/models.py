from django.db import models, transaction
from django.db.models import F
from accounts.models import Company
from django.core.exceptions import ValidationError


class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_category_per_company')
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)  # ✅ FIX
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_product_per_company')
        ]

    def __str__(self):
        return self.name


class StockHistory(models.Model):
    IN = 'IN'
    OUT = 'OUT'

    TRANSACTION_TYPE = [
        (IN, 'Stock In'),
        (OUT, 'Stock Out'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    quantity = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPE)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='stock_quantity_positive'
            )
        ]

    def clean(self):
        if not self.product_id:
            return

        if self.product.company_id != self.company_id:
            raise ValidationError("Product and Company mismatch")
        

    def save(self, *args, **kwargs):
        # ❌ update block
        if self.pk is not None:
            raise ValidationError("Updating stock history is not allowed")

        self.full_clean()

        with transaction.atomic():

            # 🔥 product row lock
            product = Product.objects.select_for_update().get(pk=self.product_id)

            # stock check
            if self.transaction_type == self.OUT:
                if product.quantity < self.quantity:
                    raise ValidationError("Not enough stock")

            # save history
            super().save(*args, **kwargs)

            # update stock
            if self.transaction_type == self.IN:
                product.quantity = F('quantity') + self.quantity
            elif self.transaction_type == self.OUT:
                product.quantity = F('quantity') - self.quantity

            product.save(update_fields=['quantity']) 

    def delete(self, *args, **kwargs):
        raise ValidationError("Deleting stock history is not allowed")
    


    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} - {self.quantity}"
    


