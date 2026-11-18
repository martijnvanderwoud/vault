"""De checks van Ward. Elke check is een module met:

- `NAAM`: de naam van de check, ook de sleutel van zijn deel in data/ward/baseline.json
- `check(hosts, referentie)`: krijgt de hostlijst en zijn deel van de referentie, en geeft
  {host: (uitkomst, details)} terug, met uitkomst `ok`, `warn` of `alarm`

Een nieuwe check komt in `CHECKS`.
"""
from . import cpu

CHECKS = [cpu]
UITKOMSTEN = ['ok', 'warn', 'alarm']  # van goed naar slecht
