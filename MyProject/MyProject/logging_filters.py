class IgnoreAssetRequests:
    """Hide static/media asset requests from Django runserver logs."""

    def filter(self, record):
        message = record.getMessage()
        return 'GET /static/' not in message and 'GET /media/' not in message
