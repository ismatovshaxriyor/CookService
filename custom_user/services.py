import geocoder
from user_agents import parse

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_location_by_ip(ip_address: str):
    g = geocoder.ip(ip_address)
    return g.city



def get_device_info(request):
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(ua_string)

    return {
        "is_mobile": user_agent.is_mobile,
        "is_tablet": user_agent.is_tablet,
        "is_pc": user_agent.is_pc,

        "browser": user_agent.browser.family,
        "browser_version": user_agent.browser.version_string,

        "os": user_agent.os.family,
        "os_version": user_agent.os.version_string,

        "device_brand": user_agent.device.brand,
        "device_model": user_agent.device.model
    }