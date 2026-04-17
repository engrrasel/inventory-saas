from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from accounts.models import Company, User


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_category_per_company')
        ]

    def __str__(self):
        return self.name


# =========================
# PRODUCT
# =========================
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)

    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_product_per_company')
        ]

    def __str__(self):
        return self.name


# =========================
# PURCHASE (LOT / INVOICE)
# =========================
class Purchase(models.Model):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    vendor_name = models.CharField(max_length=255)
    lot_number = models.CharField(max_length=100)

    purchase_date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'lot_number'],
                name='unique_lot_per_company'
            )
        ]

    def __str__(self):
        return f"{self.lot_number} - {self.vendor_name}"

    # =========================
    # APPROVE FUNCTION
    # =========================
    def approve(self, user):
        if self.status == self.APPROVED:
            raise ValidationError("Already approved")

        with transaction.atomic():
            for item in self.items.all():

                # 🔥 Stock IN create
                StockHistory.objects.create(
                    company=self.company,
                    product=item.product,
                    quantity=item.quantity,
                    transaction_type=StockHistory.IN,
                    purchase=self,
                    note=f"Lot: {self.lot_number}"
                )

                # 🔥 Buying price update
                item.product.buying_price = item.cost_price
                item.product.save(update_fields=['buying_price'])

            self.status = self.APPROVED
            self.approved_by = user
            self.approved_at = now()
            self.save(update_fields=['status', 'approved_by', 'approved_at'])


# =========================
# PURCHASE ITEM
# =========================
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.product.company_id != self.purchase.company_id:
            raise ValidationError("Product and Purchase company mismatch")

    def __str__(self):
        return f"{self.product.name} - {self.purchase.lot_number}"


# =========================
# STOCK HISTORY
# =========================
class StockHistory(models.Model):
    IN = 'IN'
    OUT = 'OUT'

    TRANSACTION_TYPE = [
        (IN, 'Stock In'),
        (OUT, 'Stock Out'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')

    # 🔥 Lot link
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)

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
    if self.pk is not None:
        raise ValidationError("Updating stock history is not allowed")

    if not self.product_id:
        raise ValidationError("Product is required")

    self.full_clean()

    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=self.product_id)

        # 🔥 OUT validation
        if self.transaction_type == self.OUT:
            if product.quantity < self.quantity:
                raise ValidationError(
                    f"Only {product.quantity} items available in stock, but you tried to use {self.quantity}."
                                )

        # 🔥 save history
        super().save(*args, **kwargs)

        # 🔥 update stock
        if self.transaction_type == self.IN:
            product.quantity = F('quantity') + self.quantity
        elif self.transaction_type == self.OUT:
            product.quantity = F('quantity') - self.quantity

        product.save(update_fields=['quantity'])

    def delete(self, *args, **kwargs):
        raise ValidationError("Deleting stock history is not allowed")

    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} - {self.quantity}"