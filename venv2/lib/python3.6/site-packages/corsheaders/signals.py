import django.dispatch

# Return Truthy values to enable a specific request.
# This allows users to build custom logic into the request handling
check_request_enabled = django.dispatch.Signal(
    providing_args=["request"]
)
