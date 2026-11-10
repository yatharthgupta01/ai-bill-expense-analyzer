"""
SQLAlchemy database models for the AI Bill & Expense Analyzer.
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    category = Column(String(100), nullable=False, default="Other", index=True)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    additional_charges = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0, index=True)
    payment_method = Column(String(100), nullable=True, default="Cash")
    currency = Column(String(10), nullable=False, default="₹")
    invoice_number = Column(String(100), nullable=True)
    source_file = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    items = relationship(
        "ExpenseItem",
        back_populates="expense",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "merchant": self.merchant,
            "date": self.date.isoformat() if self.date else None,
            "category": self.category,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "discount": self.discount,
            "additional_charges": self.additional_charges,
            "total": self.total,
            "payment_method": self.payment_method,
            "currency": self.currency,
            "invoice_number": self.invoice_number,
            "source_file": self.source_file,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items]
        }


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)

    # Relationships
    expense = relationship("Expense", back_populates="items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "expense_id": self.expense_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price
        }


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String(7), nullable=False, index=True)  # Format: "YYYY-MM"
    category = Column(String(100), nullable=True, index=True)  # None or empty represents overall monthly budget
    amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_month_category", "month", "category", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "month": self.month,
            "category": self.category,
            "amount": self.amount,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
