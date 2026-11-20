---
description: Hoe ik bij Pompkracht een pull request merge - altijd een eigen onderwerpregel, nooit de standaardregel "Merge pull request #n from ..." van GitHub
tags: [werk, pompkracht, github, git-flow]
---

# Pull requests mergen bij Pompkracht

## Regel

Een merge commit begint nooit met de standaardregel van GitHub (`Merge pull request #1016 from
Flow-Cloud-Systems/staging`). Daar staat niets in. Geef bij elke merge zelf de onderwerpregel mee:

- **Onderwerp:** de PR-titel met het PR-nummer erachter, zoals bij een squash merge:
  `PKI-1142 Nexus repository cleanup user and ingress-nginx chart removal to production (#1016)`.
- **Body:** een of twee zinnen over wat er meegaat, met de nummers van de onderliggende PR's, en de
  `Co-Authored-By`-regel.

```bash
gh pr merge <n> --merge --subject "<PR-titel> (#<n>)" --body "<samenvatting>

Co-Authored-By: ..."
```

Dit geldt voor merge commits (`develop` naar `staging`, `staging` naar `master`, terugmergen). Bij een
squash merge geeft de `--subject` al hetzelfde onderwerp; zie de [[dependabot-routine]].

Voorbeeld van hoe het moet: `f4082852` in infra (*PKI-1137 Replace ingress-nginx with Traefik in
production (#1008)*).

## Aanleiding

Op 20-11-2026 kregen #1015 (`6d4e4ca2`) en #1016 (`117f6a96`) in infra de standaardregel, omdat ik
`gh pr merge --merge` zonder `--subject` gebruikte. Die commits staan op `staging` en `master` en
blijven zo: herschrijven van gedeelde branches doen we niet.

Zie ook [[git-flow-branchregels-pompkracht]] voor de branchnamen.
