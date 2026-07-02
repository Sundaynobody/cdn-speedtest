LANG = {
    "en": {
        "lang_name": "English",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "IP Address",
        "fetching": "Fetching...",
        "failed": "Failed",
        "settings": "Settings",
        "stop": "Stop",
        "start_test": "Start Test",
        "speed_results": "Speed Results",
        "realtime_speed": "Real-time",
        "max_speed": "Max",
        "avg_speed": "Average",
        "elapsed": "Elapsed",
        "downloaded": "Downloaded",
        "ready": "Ready",
        "testing": "Testing...",
        "complete": "Complete",
        "stopped": "Stopped",
        "calculating": "Calculating...",
        "settings_title": "Node Manager",
        "node_name": "Node Name",
        "url_address": "URL Address",
        "add": "+ Add",
        "edit": "Edit",
        "delete": "Delete",
        "set_default": "Set Default",
        "close": "Close",
        "save": "Save",
        "timeout": "Connection timeout",
        "connection_failed": "Connection failed",
        "error": "Error: {msg}",
        "language": "Language",
        "name_empty": "Name cannot be empty",
        "url_empty": "URL cannot be empty",
        "no_nodes": "No nodes available",
        "export": "Export",
    },
    "zh": {
        "lang_name": "\u7b80\u4f53\u4e2d\u6587",
        "app_title": "CDN \u6d4b\u901f v{VERSION}",
        "ip_address": "IP \u5730\u5740",
        "fetching": "\u83b7\u53d6\u4e2d...",
        "failed": "\u83b7\u53d6\u5931\u8d25",
        "settings": "\u8bbe\u7f6e",
        "stop": "\u505c\u6b62",
        "start_test": "\u5f00\u59cb\u6d4b\u901f",
        "speed_results": "\u6d4b\u901f\u7ed3\u679c",
        "realtime_speed": "\u5b9e\u65f6\u901f\u7387",
        "max_speed": "\u6700\u9ad8\u901f\u7387",
        "avg_speed": "\u5e73\u5747\u901f\u7387",
        "elapsed": "\u5df2\u7528\u65f6\u95f4",
        "downloaded": "\u5df2\u4e0b\u8f7d",
        "ready": "\u5c31\u7eea",
        "testing": "\u6d4b\u901f\u4e2d...",
        "complete": "\u6d4b\u901f\u5b8c\u6210",
        "stopped": "\u5df2\u505c\u6b62",
        "calculating": "\u8ba1\u7b97\u4e2d...",
        "settings_title": "\u8282\u70b9\u7ba1\u7406",
        "node_name": "\u8282\u70b9\u540d\u79f0",
        "url_address": "URL \u5730\u5740",
        "add": "+ \u65b0\u589e",
        "edit": "\u7f16\u8f91",
        "delete": "\u5220\u9664",
        "set_default": "\u8bbe\u4e3a\u9ed8\u8ba4",
        "close": "\u5173\u95ed",
        "save": "\u4fdd\u5b58",
        "timeout": "\u8fde\u63a5\u8d85\u65f6",
        "connection_failed": "\u8fde\u63a5\u5931\u8d25",
        "error": "\u9519\u8bef: {msg}",
        "language": "\u8bed\u8a00",
        "name_empty": "\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a",
        "url_empty": "URL \u4e0d\u80fd\u4e3a\u7a7a",
        "no_nodes": "\u6ca1\u6709\u53ef\u7528\u8282\u70b9",
        "export": "\u5bfc\u51fa",
    },
}

_supported_langs = sorted(LANG.keys(), key=lambda l: 0 if l == "en" else 1)
_current_lang = "en"

def set_language(lang):
    global _current_lang
    if lang in LANG:
        _current_lang = lang

def t(key, **kwargs):
    text = LANG.get(_current_lang, {}).get(key, LANG.get("en", {}).get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text
