#!/usr/bin/python3
"""Read-only nagaan op één host, voor Ward: een vast commando per onderwerp, nooit iets anders.

    nagaan.py HOST ONDERWERP

ONDERWERP is een van de sleutels van COMMANDO'S. HOST moet in ~/.ssh/config staan. Zo krijgt Ward
geen vrije SSH: de allowlist laat alleen dit script toe, en het script kiest het commando.
Plan: gebieden/werk/ward-plan.md, stap 3.
"""
import os
import sys

# Met `python3 -I` staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ssh  # noqa: E402

COMMANDO_S = {
    'cpu': "grep -E '^(model name|flags)' /proc/cpuinfo | sort | uniq -c",
    'lscpu': 'lscpu',
    'uname': 'uname -a',
    'uptime': 'uptime',
    'dmi': 'cat /sys/class/dmi/id/sys_vendor /sys/class/dmi/id/product_name 2>/dev/null',
}
MAX = 20000  # tekens per stroom


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in COMMANDO_S:
        raise SystemExit('gebruik: nagaan.py HOST {%s}' % ','.join(COMMANDO_S))
    host, onderwerp = sys.argv[1:]
    if host not in ssh.hosts():
        raise SystemExit('onbekende host: %s (niet in %s)' % (host, ssh.SSH_CONFIG))
    returncode, stdout, stderr = ssh.uitvoeren(host, COMMANDO_S[onderwerp])
    print('$ %s  (op %s, exit %d)' % (COMMANDO_S[onderwerp], host, returncode))
    print(stdout[:MAX], end='')
    if stderr.strip():
        print('--- stderr\n' + stderr[:MAX], end='')
    return 0 if returncode == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
