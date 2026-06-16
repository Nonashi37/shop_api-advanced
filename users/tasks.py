# users/tasks.py
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# --- 1. Async E-Commerce Task via .delay() ---
@shared_task
def generate_order_invoice_pdf_task(order_id: int, customer_email: str):
    """
    Triggered manually via .delay() right after a successful checkout.
    Compiling PDFs and calculating taxes is slow; offloading this keeps 
    the checkout response time under 50 milliseconds.
    """
    logger.info(f"🧾 Generating PDF Invoice for Order #{order_id}...")
    
    # Simulate heavy file generation overhead
    import time
    time.sleep(4) 
    
    # In real life, you'd attach the file here
    send_mail(
        subject=f"Your Receipt for Order #{order_id}",
        message="Thank you for your purchase! Your invoice is attached.",
        from_email="billing@advancedshop.com",
        recipient_list=[customer_email],
        fail_silently=False,
    )
    logger.info(f"Invoice sent to {customer_email} for Order #{order_id}.")
    return f"Invoice_#{order_id}_Processed"


# --- 2. Auth SMTP Task via Redis Trigger ---
@shared_task
def send_shop_otp_email_task(email: str, code: str):
    """
    Asynchronously fires the 6-digit login token. 
    Matches your Redis caching layer perfectly.
    """
    send_mail(
        subject="Your Shop Access Code",
        message=f"Use this single-use token to verify your login session: {code}\nExpires in 5 minutes.",
        from_email="auth@advancedshop.com",
        recipient_list=[email],
        fail_silently=False,
    )
    return f"Auth OTP dispatched to {email}"


# --- 3. Automated Cron Task via Celery Beat ---
@shared_task
def cleanup_expired_carts_task():
    """
    Runs automatically on a schedule to clear out abandoned checkouts
    and return reserved items back to the active shop inventory.
    """
    logger.info("🛒 Scanning database for abandoned, unpaid carts...")
    
    # Mock data lookup logic for your shopping cart models
    # e.g., Cart.objects.filter(updated_at__lt=timezone.now() - timedelta(hours=24), is_paid=False).delete()
    
    logger.info("[CRON] Database optimization complete: Abandoned sessions expunged.")
    return "Inventory sync successful."