from .views import withdrawal_api_view, settlement_batch_api_view, settlement_entries_api_view, air_kafka_api_view
from  django.urls import path


urlpatterns = [
    path("withdrawal/", withdrawal_api_view, name='withdrawal'),
    path("settlement/", settlement_batch_api_view, name='settle_batch'),
    path("settlement/entries/", settlement_entries_api_view, name='settle_entries'),
    path("air_kafka/", air_kafka_api_view)
]


from urllib.parse import quote, unquote

value = "WTH|202508040200496000755DFTY170000000002057565701"

# # Encode for URL
# encoded = quote(value, safe="")  
# print(encoded)
# # Output: WTH%7C202508040200496000755DFTY170000000002057565701

# # Decode back
# decoded = unquote(encoded)
# print(decoded)
# # Output: WTH|202508040200496000755DFTY170000000002057565701

