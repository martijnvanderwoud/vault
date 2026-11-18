#!/usr/bin/python3
"""PreToolUse-hook voor de Gmail-tools van Ward: alleen mail aan mij komt erdoor.

Ward leest uitvoer van hosts, en een allowlist bepaalt niet aan wie `send_message` mailt. Daarom
weigert deze hook elke Gmail-tool behalve `send_message`, en `send_message` zodra `to`, `cc` of
`bcc` een ander adres bevat dan ONTVANGER, `to` leeg is of er een `draftId` is (een concept wordt
verstuurd zoals het is, met zijn eigen ontvangers). Een reply in een bestaande thread weigert hij
ook. Bij een fout in de invoer weigert hij, nooit stil doorlaten.
Achtergrond: gebieden/werk/ward-bewaking/ward-bewaking-logboek.md, stap 3.
"""
import json
import sys

ONTVANGER = 'martijn@crimsoncricket.nl'
SEND = 'mcp__claude_ai_Gmail__send_message'


def bezwaar(invoer):
    """Waarom deze tool-aanroep niet mag, of None als hij mag."""
    tool = invoer.get('tool_name')
    if tool != SEND:
        return 'Ward mag alleen %s gebruiken, niet %s' % (SEND, tool)
    velden = invoer.get('tool_input') or {}
    for veld in ('draftId', 'replyThreadId', 'replyToMessageId'):
        if velden.get(veld):
            return 'Ward verstuurt geen concept en antwoordt niet in een thread (%s)' % veld
    if not velden.get('to'):
        return '`to` ontbreekt'
    for veld in ('to', 'cc', 'bcc'):
        adressen = velden.get(veld) or []
        if isinstance(adressen, str):
            adressen = [adressen]
        anders = [a for a in adressen if str(a).strip().lower() != ONTVANGER]
        if anders:
            return 'Ward mailt alleen aan %s, niet aan %s (%s)' % (ONTVANGER, ', '.join(map(str, anders)), veld)
    return None


def main():
    try:
        reden = bezwaar(json.load(sys.stdin))
    except Exception as e:  # onleesbare invoer: weigeren
        reden = 'hook kon de invoer niet lezen: %s' % e
    if reden:
        json.dump({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                          'permissionDecisionReason': reden}}, sys.stdout)


if __name__ == '__main__':
    main()
