"""
General helper functions for the application.
"""


def safe_int(value, default=0):
    """
    Safely convert value to int, return default if conversion fails.
    
    Args:
        value: The value to convert to int
        default: Default value to return if conversion fails (default: 0)
        
    Returns:
        int: Converted integer or default value
        
    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("invalid", 0)
        0
        >>> safe_int(None, -1)
        -1
    """
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default
