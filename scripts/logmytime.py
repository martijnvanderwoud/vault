"""Gedeelde toegang tot de LogMyTime API (alleen lezen), voor uren.py en uren_naar_youtrack.py.

De sleutel komt uit LOGMYTIME_API_KEY in ~/vault/.env en wordt nooit getoond.
Limiet: 500 requests per 24 uur per account, geen parallelle requests.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = 'https://api.logmytime.de/V1/Api.svc'
TZ = ZoneInfo('Europe/Amsterdam')


def key():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('LOGMYTIME_API_KEY='):
            sleutel = line.split('=', 1)[1].strip()
            if sleutel:
                return sleutel
    raise SystemExit('LOGMYTIME_API_KEY ontbreekt of is leeg in ' + path)


def get_all(resource, params):
    """Haalt alle pagina's van een OData-resource op (max 10.000 entities per response)."""
    url = BASE + '/' + resource + '?' + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    headers = {'X-LogMyTimeApiKey': key(), 'Accept': 'application/json'}
    resultaten = []
    while url:
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=headers)))['d']
        except urllib.error.HTTPError as e:
            raise SystemExit('LogMyTime API gaf HTTP %s %s voor %s' % (e.code, e.reason, resource))
        if isinstance(data, list):
            resultaten += data
            url = None
        else:
            resultaten += data['results']
            url = data.get('__next')
    return resultaten


def odata_datum(d):
    return "datetime'%sT00:00:00'" % d.isoformat()


def lokale_datum(ms):
    return datetime.fromtimestamp(int(ms[6:-2]) / 1000, timezone.utc).astimezone(TZ).date()
