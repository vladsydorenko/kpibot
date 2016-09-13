class StopExecution(Exception):
    pass


class SendError(Exception):
    pass


class MultipleResults(Exception):
    """Custom exception, to handle multiple returned results from API
    (for groups and teachers)"""
    pass
