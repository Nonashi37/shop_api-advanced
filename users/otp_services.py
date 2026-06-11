# users/otp_services.py
import logging
from common.redis_client import redis_client

logger = logging.getLogger(__name__)

OTP_EXPIRATION_SECONDS = 300 # Condition 1: 5 minutes exact lifetime

def save_otp_code(identifier: str, code: str) -> None:
    """
    Saves a 6-digit confirmation code tied to a user identifier (phone or email) 
    with a strict 5-minute TTL.
    """
    redis_key = f"otp:{identifier}"
    
    # 'setex' stands for "SET with EXpiration". It sets the key and time atomically!
    redis_client.setex(
        name=redis_key,
        time=OTP_EXPIRATION_SECONDS,
        value=str(code)
    )
    logger.info(f"OTP code stored in Redis for {identifier}. Expires in 5m.")


def verify_and_consume_otp(identifier: str, input_code: str) -> bool:
    """
    Validates the input OTP code against Redis. 
    Vaporizes the key immediately if it matches.
    """
    redis_key = f"otp:{identifier}"
    
    # 1. Fetch the code from RAM
    stored_code = redis_client.get(redis_key)
    
    # If the key expired or doesn't exist, Redis returns None
    if not stored_code:
        return False
        
    # 2. Check if the user typed the right digits
    if stored_code == str(input_code):
        # Condition 2: Delete from Redis immediately upon successful use
        redis_client.delete(redis_key)
        logger.info(f"OTP consumed successfully for {identifier}. Key deleted.")
        return True
        
    # If they typed it wrong, we DON'T delete it, allowing them to try again until the 5 minutes run out
    return False



# Fi