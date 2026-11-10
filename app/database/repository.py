"""
Repository pattern for Expense and Budget database operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_, and_

from app.database.models import Expense, ExpenseItem, Budget
from app.database.database import get_db

class ExpenseRepository:
    """Repository handling all expense and expense item persistence."""

    @staticmethod
    def create_expense(data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Expense:
        """Create a new expense with optional line items."""
        with get_db() as db:
            expense_date = data.get("date")
            if isinstance(expense_date, str):
                expense_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
            elif not isinstance(expense_date, date):
                expense_date = date.today()

            expense = Expense(
                merchant=str(data.get("merchant", "Unknown Merchant")).strip(),
                date=expense_date,
                category=str(data.get("category", "Other")).strip(),
                subtotal=float(data.get("subtotal", 0.0) or 0.0),
                tax=float(data.get("tax", 0.0) or 0.0),
                discount=float(data.get("discount", 0.0) or 0.0),
                additional_charges=float(data.get("additional_charges", 0.0) or 0.0),
                total=float(data.get("total", 0.0) or 0.0),
                payment_method=str(data.get("payment_method", "Cash")).strip(),
                currency=str(data.get("currency", "₹")).strip(),
                invoice_number=data.get("invoice_number"),
                source_file=data.get("source_file"),
                notes=data.get("notes")
            )
            db.add(expense)
            db.flush()  # populate expense.id

            if items:
                for item_dict in items:
                    name = str(item_dict.get("item_name", "")).strip()
                    if not name:
                        continue
                    qty = float(item_dict.get("quantity", 1.0) or 1.0)
                    price = float(item_dict.get("unit_price", 0.0) or 0.0)
                    tot = float(item_dict.get("total_price", 0.0) or (qty * price))
                    
                    item = ExpenseItem(
                        expense_id=expense.id,
                        item_name=name,
                        quantity=qty,
                        unit_price=price,
                        total_price=tot
                    )
                    db.add(item)
            
            db.commit()
            db.refresh(expense)
            return expense

    @staticmethod
    def get_expense_by_id(expense_id: int) -> Optional[Expense]:
        """Fetch a single expense by ID with line items loaded."""
        with get_db() as db:
            return db.query(Expense).filter(Expense.id == expense_id).first()

    @staticmethod
    def update_expense(expense_id: int, data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[Expense]:
        """Update an existing expense and refresh its line items."""
        with get_db() as db:
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if not expense:
                return None

            if "merchant" in data:
                expense.merchant = str(data["merchant"]).strip()
            if "date" in data:
                d = data["date"]
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                expense.date = d
            if "category" in data:
                expense.category = str(data["category"]).strip()
            if "subtotal" in data:
                expense.subtotal = float(data["subtotal"] or 0.0)
            if "tax" in data:
                expense.tax = float(data["tax"] or 0.0)
            if "discount" in data:
                expense.discount = float(data["discount"] or 0.0)
            if "additional_charges" in data:
                expense.additional_charges = float(data["additional_charges"] or 0.0)
            if "total" in data:
                expense.total = float(data["total"] or 0.0)
            if "payment_method" in data:
                expense.payment_method = str(data["payment_method"]).strip()
            if "currency" in data:
                expense.currency = str(data["currency"]).strip()
            if "invoice_number" in data:
                expense.invoice_number = data["invoice_number"]
            if "source_file" in data:
                expense.source_file = data["source_file"]
            if "notes" in data:
                expense.notes = data["notes"]

            # Replace items if items list is provided
            if items is not None:
                db.query(ExpenseItem).filter(ExpenseItem.expense_id == expense.id).delete()
                for item_dict in items:
                    name = str(item_dict.get("item_name", "")).strip()
                    if not name:
                        continue
                    qty = float(item_dict.get("quantity", 1.0) or 1.0)
                    price = float(item_dict.get("unit_price", 0.0) or 0.0)
                    tot = float(item_dict.get("total_price", 0.0) or (qty * price))
                    
                    item = ExpenseItem(
                        expense_id=expense.id,
                        item_name=name,
                        quantity=qty,
                        unit_price=price,
                        total_price=tot
                    )
                    db.add(item)

            db.commit()
            db.refresh(expense)
            return expense

    @staticmethod
    def delete_expense(expense_id: int) -> bool:
        """Delete an expense by ID."""
        with get_db() as db:
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if expense:
                db.delete(expense)
                db.commit()
                return True
            return False

    @staticmethod
    def list_expenses(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        payment_method: Optional[str] = None,
        order_by: str = "date_desc",
        limit: Optional[int] = None
    ) -> List[Expense]:
        """Query expenses with comprehensive filters and sorting."""
        with get_db() as db:
            query = db.query(Expense)

            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)
            if category and category != "All":
                query = query.filter(Expense.category == category)
            if payment_method and payment_method != "All":
                query = query.filter(Expense.payment_method == payment_method)
            if min_amount is not None:
                query = query.filter(Expense.total >= min_amount)
            if max_amount is not None:
                query = query.filter(Expense.total <= max_amount)
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Expense.merchant.ilike(term),
                        Expense.category.ilike(term),
                        Expense.invoice_number.ilike(term),
                        Expense.notes.ilike(term)
                    )
                )

            if order_by == "date_desc":
                query = query.order_by(desc(Expense.date), desc(Expense.id))
            elif order_by == "date_asc":
                query = query.order_by(asc(Expense.date), asc(Expense.id))
            elif order_by == "total_desc":
                query = query.order_by(desc(Expense.total))
            elif order_by == "total_asc":
                query = query.order_by(asc(Expense.total))
            else:
                query = query.order_by(desc(Expense.date))

            if limit:
                query = query.limit(limit)

            return query.all()

    @staticmethod
    def get_summary_stats(start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculate high-level summary KPIs for the given date range."""
        with get_db() as db:
            query = db.query(
                func.sum(Expense.total).label("total_spending"),
                func.count(Expense.id).label("transaction_count"),
                func.avg(Expense.total).label("average_expense"),
                func.max(Expense.total).label("highest_expense")
            )
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)

            res = query.first()
            total = float(res.total_spending or 0.0)
            count = int(res.transaction_count or 0)
            avg = float(res.average_expense or 0.0)
            highest = float(res.highest_expense or 0.0)

            # Determine top category
            top_cat_query = db.query(
                Expense.category,
                func.sum(Expense.total).label("cat_total")
            )
            if start_date:
                top_cat_query = top_cat_query.filter(Expense.date >= start_date)
            if end_date:
                top_cat_query = top_cat_query.filter(Expense.date <= end_date)

            top_cat_res = top_cat_query.group_by(Expense.category).order_by(desc("cat_total")).first()
            top_category = top_cat_res[0] if top_cat_res else "None"
            top_category_amount = float(top_cat_res[1] or 0.0) if top_cat_res else 0.0

            return {
                "total_spending": round(total, 2),
                "transaction_count": count,
                "average_expense": round(avg, 2),
                "highest_expense": round(highest, 2),
                "top_category": top_category,
                "top_category_amount": round(top_category_amount, 2)
            }

    @staticmethod
    def get_category_breakdown(start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get aggregate spending, count, and percentage per category."""
        with get_db() as db:
            query = db.query(
                Expense.category,
                func.sum(Expense.total).label("total"),
                func.count(Expense.id).label("count")
            )
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)

            results = query.group_by(Expense.category).order_by(desc("total")).all()
            total_sum = sum(float(r[1] or 0.0) for r in results)

            breakdown = []
            for cat, amount, count in results:
                amt = float(amount or 0.0)
                pct = (amt / total_sum * 100.0) if total_sum > 0 else 0.0
                breakdown.append({
                    "category": cat,
                    "total": round(amt, 2),
                    "count": int(count),
                    "percentage": round(pct, 1)
                })
            return breakdown

    @staticmethod
    def get_monthly_spending(months_back: int = 6) -> List[Dict[str, Any]]:
        """Get spending totals grouped by month (YYYY-MM)."""
        with get_db() as db:
            # Group by strftime for SQLite
            query = db.query(
                func.strftime("%Y-%m", Expense.date).label("month"),
                func.sum(Expense.total).label("total"),
                func.count(Expense.id).label("count")
            ).group_by("month").order_by(asc("month"))

            results = query.all()
            data = []
            for m, tot, cnt in results:
                if m:
                    data.append({
                        "month": m,
                        "total": round(float(tot or 0.0), 2),
                        "count": int(cnt)
                    })
            if months_back and len(data) > months_back:
                data = data[-months_back:]
            return data

    @staticmethod
    def get_daily_trend(start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get daily spend totals for trendline visualization."""
        with get_db() as db:
            query = db.query(
                Expense.date,
                func.sum(Expense.total).label("total"),
                func.count(Expense.id).label("count")
            )
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)

            results = query.group_by(Expense.date).order_by(asc(Expense.date)).all()
            return [
                {
                    "date": d.isoformat() if isinstance(d, date) else str(d),
                    "total": round(float(tot or 0.0), 2),
                    "count": int(cnt)
                }
                for d, tot, cnt in results
            ]

    @staticmethod
    def get_merchant_breakdown(start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top merchants by total spending."""
        with get_db() as db:
            query = db.query(
                Expense.merchant,
                func.sum(Expense.total).label("total"),
                func.count(Expense.id).label("count")
            )
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)

            results = query.group_by(Expense.merchant).order_by(desc("total")).limit(limit).all()
            return [
                {
                    "merchant": m,
                    "total": round(float(tot or 0.0), 2),
                    "count": int(cnt)
                }
                for m, tot, cnt in results
            ]

    @staticmethod
    def get_day_of_week_breakdown(start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Analyze spending differences between weekdays and weekends."""
        with get_db() as db:
            query = db.query(Expense.date, Expense.total)
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)

            rows = query.all()
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_totals = {d: 0.0 for d in days}
            day_counts = {d: 0 for d in days}

            weekday_total = 0.0
            weekend_total = 0.0

            for exp_date, total in rows:
                if not exp_date:
                    continue
                day_name = exp_date.strftime("%A")
                val = float(total or 0.0)
                day_totals[day_name] += val
                day_counts[day_name] += 1
                if day_name in ["Saturday", "Sunday"]:
                    weekend_total += val
                else:
                    weekday_total += val

            return {
                "day_totals": day_totals,
                "day_counts": day_counts,
                "weekday_total": round(weekday_total, 2),
                "weekend_total": round(weekend_total, 2)
            }

    @staticmethod
    def clear_all_expenses():
        """Clear all expense records for testing / reset."""
        with get_db() as db:
            db.query(ExpenseItem).delete()
            db.query(Expense).delete()
            db.commit()


class BudgetRepository:
    """Repository handling monthly overall and category-specific budgets."""

    @staticmethod
    def set_budget(month: str, amount: float, category: Optional[str] = None) -> Budget:
        """Set or update budget for a given month and category (None = overall)."""
        cat_key = category.strip() if category and category != "Overall" else None
        with get_db() as db:
            budget = db.query(Budget).filter(
                Budget.month == month,
                Budget.category == cat_key
            ).first()

            if budget:
                budget.amount = float(amount)
            else:
                budget = Budget(
                    month=month,
                    category=cat_key,
                    amount=float(amount)
                )
                db.add(budget)

            db.commit()
            db.refresh(budget)
            return budget

    @staticmethod
    def get_budgets(month: str) -> List[Budget]:
        """Fetch all budgets configured for a given month."""
        with get_db() as db:
            return db.query(Budget).filter(Budget.month == month).all()

    @staticmethod
    def get_budget_status(month: str) -> Dict[str, Any]:
        """
        Compare configured budgets against actual expenses for the month.
        Calculates: budget, spent, remaining, percentage used, warning (>85%), exceeded (>100%).
        """
        try:
            year, m_num = [int(p) for p in month.split("-")]
            start_date = date(year, m_num, 1)
            next_m = m_num + 1 if m_num < 12 else 1
            next_y = year if m_num < 12 else year + 1
            end_date = date(next_y, next_m, 1) - timedelta(days=1)
        except Exception:
            start_date = date.today().replace(day=1)
            end_date = date.today()

        with get_db() as db:
            # Actual spent overall
            overall_spent_res = db.query(func.sum(Expense.total)).filter(
                Expense.date >= start_date,
                Expense.date <= end_date
            ).scalar()
            overall_spent = float(overall_spent_res or 0.0)

            # Actual spent per category
            cat_spent_rows = db.query(
                Expense.category,
                func.sum(Expense.total)
            ).filter(
                Expense.date >= start_date,
                Expense.date <= end_date
            ).group_by(Expense.category).all()
            cat_spent_dict = {row[0]: float(row[1] or 0.0) for row in cat_spent_rows}

            # Configured budgets
            budgets = db.query(Budget).filter(Budget.month == month).all()

            overall_budget_obj = next((b for b in budgets if b.category is None), None)
            overall_budget_amount = overall_budget_obj.amount if overall_budget_obj else 0.0

            overall_pct = (overall_spent / overall_budget_amount * 100.0) if overall_budget_amount > 0 else 0.0
            overall_rem = max(0.0, overall_budget_amount - overall_spent) if overall_budget_amount > 0 else 0.0

            overall_status = {
                "budget": round(overall_budget_amount, 2),
                "spent": round(overall_spent, 2),
                "remaining": round(overall_rem, 2),
                "percentage": round(overall_pct, 1),
                "is_warning": overall_pct >= 85.0 and overall_pct < 100.0,
                "is_exceeded": overall_pct >= 100.0
            }

            category_statuses = []
            configured_categories = {b.category: b.amount for b in budgets if b.category is not None}
            # Include all categories that have either a budget or spending
            all_cat_keys = set(configured_categories.keys()).union(cat_spent_dict.keys())

            for cat in sorted(all_cat_keys):
                cat_budget = configured_categories.get(cat, 0.0)
                cat_spent = cat_spent_dict.get(cat, 0.0)
                pct = (cat_spent / cat_budget * 100.0) if cat_budget > 0 else 0.0
                rem = max(0.0, cat_budget - cat_spent) if cat_budget > 0 else 0.0

                category_statuses.append({
                    "category": cat,
                    "budget": round(cat_budget, 2),
                    "spent": round(cat_spent, 2),
                    "remaining": round(rem, 2),
                    "percentage": round(pct, 1),
                    "is_warning": pct >= 85.0 and pct < 100.0,
                    "is_exceeded": pct >= 100.0
                })

            return {
                "month": month,
                "overall": overall_status,
                "categories": category_statuses
            }
