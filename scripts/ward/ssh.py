"""SSH naar de hosts voor Ward: de hostlijst uit ~/.ssh/config en één commando op alle hosts tegelijk.

Geen wachtwoordprompt (BatchMode) en een korte timeout: een host die niet antwoordt, levert een
fout op in plaats van een hangende run. De sleutels komen uit de agent, die ze onder launchd zelf
uit de keychain laadt (UseKeychain en AddKeysToAgent, zie stap 1 van gebieden/werk/ward-plan.md).
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

SSH_CONFIG = Path.home() / '.ssh/config'
SSH = '/usr/bin/ssh'
OPTIES = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
TIMEOUT = 45  # seconden per host, ruim genoeg voor een ProxyJump


def hosts(config=SSH_CONFIG):
    """De `Host`-namen uit de ssh-config zonder wildcard of negatie, in volgorde."""
    result = []
    for regel in Path(config).read_text().splitlines():
        delen = regel.split('#', 1)[0].split()
        if len(delen) < 2 or delen[0].lower() != 'host':
            continue
        for naam in delen[1:]:
            if not any(c in naam for c in '*?!') and naam not in result:
                result.append(naam)
    return result


def uitvoeren(host, commando):
    """(returncode, stdout, stderr) van `commando` op `host`. Returncode 255 is een fout van ssh
    zelf, zoals een onbereikbare host of een geweigerde sleutel."""
    try:
        proc = subprocess.run([SSH] + OPTIES + [host, commando], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 255, '', 'geen antwoord binnen %d seconden' % TIMEOUT
    return proc.returncode, proc.stdout, proc.stderr


def op_alle(hosts, commando):
    """{host: (returncode, stdout, stderr)}, alle hosts tegelijk."""
    with ThreadPoolExecutor(max_workers=max(1, len(hosts))) as pool:
        return dict(zip(hosts, pool.map(lambda h: uitvoeren(h, commando), hosts)))
