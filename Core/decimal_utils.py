from decimal import Decimal, InvalidOperation
from functools import wraps

def require_decimal(*param_names):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                for name in param_names:
                    if name in kwargs:
                        if kwargs[name] is None:
                            continue
                        if isinstance(kwargs[name], Decimal):
                            continue
                        kwargs[name] = Decimal(str(kwargs[name]))
                return func(*args, **kwargs)
            except (ValueError, InvalidOperation) as e:
                raise ValueError(f"Invalid decimal value for parameter '{name}'")
        return wrapper
    return decorator

def validate_positive(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, Decimal) and result <= 0:
            raise ValueError("Value must be positive")
        return result
    return wrapper
