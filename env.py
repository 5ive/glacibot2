""" Stores global-scope variables """

# Standard Modules
MODULES = {
    'slack': None,
    'mysql': None
}

# Standard Utilities
UTILS = {
    'manager': None,
    'slack': None,
    'mysql': None
}

# Statistics Tracking
STATS = {
    'birth': 0,
    'connected_at': 0,
    'latency': []
}

# Global Storage
GLOBAL = {
    'commands': {},
    'loop': None,
    'socket': None
}

# Configuration
CONSTANTS = {
    'sql_user': 'glacibot',
    'sql_database': 'glacibot'
}

# Administration
ADMIN = {
    'admins': []
}
