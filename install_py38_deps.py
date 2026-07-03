"""Install Python 3.8 dependencies with SSL + proxy workaround."""
import ssl, sys, os, winreg

# Disable proxy
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
    0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
old_proxy = winreg.QueryValueEx(key, 'ProxyEnable')[0]
winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
winreg.CloseKey(key)

# Patch SSL
import pip._vendor.urllib3.util.ssl_ as ussl
_orig = ussl._ssl_wrap_socket_impl
def _patched(sock, ssl_context, tls_in_tls, server_hostname=None):
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return _orig(sock, ssl_context, tls_in_tls, server_hostname)
ussl._ssl_wrap_socket_impl = _patched

PKGS = ["ttkbootstrap", "PyInstaller", "Pillow"]
import pip
pip.main(["install"] + PKGS + ["--trusted-host", "pypi.org"])

# Restore proxy
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
    0, winreg.KEY_SET_VALUE)
winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, old_proxy)
winreg.CloseKey(key)
print("Done")
