def calculate_error_rate(total_requests, failed_requests):

    if total_requests == 0:
        return 0

    return (failed_requests / total_requests) * 100
