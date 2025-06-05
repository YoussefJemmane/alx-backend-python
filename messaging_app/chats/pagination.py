from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    A standard pagination class that paginates by 20 items per page.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

