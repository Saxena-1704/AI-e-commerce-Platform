import unittest
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.api.orders import checkout
from backend.app.models.category import Category
from backend.app.models.cart import Cart
from backend.app.models.cart_item import CartItem
from backend.app.models.order import Order
from backend.app.models.order_item import OrderItem
from backend.app.models.payment import Payment
from backend.app.models.product import Product
from backend.app.models.role import UserRole
from backend.app.models.user import User
from backend.app.services.payment_service import fail_payment, finalize_payment


class PaymentLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        role = UserRole(role_name="customer")
        category = Category(category_name="Audio", url_slug="audio")
        self.db.add_all([role, category])
        self.db.flush()
        user = User(
            role_id=role.id,
            full_name="Test Customer",
            email=f"customer-{id(self)}@example.com",
            password_hash="not-used",
        )
        product = Product(
            product_name="Headphones",
            url_slug=f"headphones-{id(self)}",
            category_id=category.id,
            price=Decimal("10.00"),
            stock_quantity=5,
        )
        self.db.add_all([user, product])
        self.db.flush()
        order = Order(
            order_number=f"ORD-{id(self)}",
            user_id=user.id,
            subtotal=Decimal("20.00"),
            discount_amount=Decimal("0.00"),
            shipping_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("20.00"),
            status="pending_payment",
        )
        self.db.add(order)
        self.db.flush()
        self.db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.product_name,
            price=product.price,
            quantity=2,
            total_amount=Decimal("20.00"),
        ))
        self.payment = Payment(
            order_id=order.id,
            provider_order_id=f"order_{id(self)}",
            amount=Decimal("20.00"),
            currency="INR",
            status="created",
        )
        self.db.add(self.payment)
        self.db.commit()
        self.db.refresh(self.payment)
        self.product = product
        self.order = order
        self.user = user

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        # Keep each test independent while reusing the in-memory database.
        with self.engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())

    def test_successful_payment_decreases_stock_and_marks_order_paid(self):
        finalize_payment(self.db, self.payment, "pay_success")

        self.db.refresh(self.product)
        self.db.refresh(self.order)
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(self.order.status, "paid")

    def test_creating_order_does_not_decrease_stock(self):
        cart = Cart(user_id=self.user.id, status="active")
        self.db.add(cart)
        self.db.flush()
        self.db.add(CartItem(cart_id=cart.id, product_id=self.product.id, quantity=2))
        self.db.commit()

        checkout(self.db, self.user)

        self.db.refresh(self.product)
        self.assertEqual(self.product.stock_quantity, 5)

    def test_failed_payment_does_not_decrease_stock(self):
        fail_payment(self.db, self.payment)

        self.db.refresh(self.product)
        self.db.refresh(self.order)
        self.assertEqual(self.product.stock_quantity, 5)
        self.assertEqual(self.payment.status, "failed")
        self.assertEqual(self.order.status, "payment_failed")

    def test_duplicate_successful_verification_and_webhook_decrease_once(self):
        finalize_payment(self.db, self.payment, "pay_success")
        finalize_payment(self.db, self.payment, "pay_success")

        self.db.refresh(self.product)
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(self.order.status, "paid")


if __name__ == "__main__":
    unittest.main()
