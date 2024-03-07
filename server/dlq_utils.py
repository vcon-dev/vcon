# Dead Letter Queue utils

def get_ingress_list_dlq_name(ingress_list: str) -> str:
    return f"DLQ:{ingress_list}"
