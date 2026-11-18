"""CPU-check voor Java4Shell (CVE-2026-114938, PKI-1132): het CPU-model en `avx512vbmi` per host.

`alarm` zodra `avx512vbmi` in de flags staat, want dan zijn we kwetsbaar en is de hotfix uit
PKI-1132 nodig. `warn` bij een ander CPU-model dan in de referentie (nog niet gevaarlijk, wel een
vroeg teken dat TransIP iets verandert) en bij een host die niet antwoordt.
"""
import ssh

NAAM = 'cpu'
COMMANDO = "grep -E '^(model name|flags)' /proc/cpuinfo"


def beoordeel(returncode, stdout, stderr, referentie):
    """(uitkomst, details) voor de uitvoer van COMMANDO op één host."""
    if returncode == 255:
        fout = (stderr.strip().splitlines() or ['onbekende ssh-fout'])[-1]
        return 'warn', 'onbereikbaar: %s' % fout
    modellen, vbmi = set(), False
    for regel in stdout.splitlines():
        sleutel, _, waarde = regel.partition(':')
        if sleutel.strip() == 'model name':
            modellen.add(waarde.strip())
        elif sleutel.strip() == 'flags' and 'avx512vbmi' in waarde.split():
            vbmi = True
    if not modellen:
        return 'warn', 'geen CPU-model in /proc/cpuinfo (exit %d)' % returncode
    model = ', '.join(sorted(modellen))
    if vbmi and not referentie['avx512vbmi']:
        return 'alarm', 'avx512vbmi aanwezig (%s): kwetsbaar voor Java4Shell, hotfix uit PKI-1132 nodig' % model
    if vbmi != referentie['avx512vbmi']:
        return 'warn', 'avx512vbmi %s, verwacht %s (%s)' % (
            'aanwezig' if vbmi else 'afwezig', 'aanwezig' if referentie['avx512vbmi'] else 'afwezig', model)
    if modellen != {referentie['model']}:
        return 'warn', 'ander CPU-model: %s, verwacht %s' % (model, referentie['model'])
    return 'ok', model


def check(hosts, referentie):
    return {host: beoordeel(*uitvoer, referentie) for host, uitvoer in ssh.op_alle(hosts, COMMANDO).items()}
