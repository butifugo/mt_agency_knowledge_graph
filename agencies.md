# Montana State Government Agencies

This file contains a comprehensive list of all Montana state government agencies and their official mt.gov domain websites. The crawler will automatically process all agencies listed here.

## Format

Each agency is listed with:
- **Agency Name** - Official name of the agency
- **URL** - Official mt.gov website URL
- **Folder** - Output folder name within the knowledge directory

---

## State Agencies

| Agency Name | URL | Folder |
|------------|-----|--------|
| Administration | https://doa.mt.gov/ | administration |
| Agriculture | https://agr.mt.gov/ | agriculture |
| Arts Council | https://art.mt.gov/ | arts-council |
| Auditor | https://csimt.gov/ | auditor |
| Commerce | https://commerce.mt.gov/ | commerce |
| Corrections | https://cor.mt.gov/ | corrections |
| Environmental Quality | https://deq.mt.gov/ | environmental-quality |
| Fish, Wildlife & Parks | https://fwp.mt.gov/ | fish-wildlife-parks |
| Governor's Office | https://governor.mt.gov/ | governor |
| Higher Education, Commissioner of | https://mus.edu/che | higher-education |
| Human Resources | https://hr.mt.gov/ | human-resources |
| Montana Historical Society | https://mhs.mt.gov/ | historical-society |
| Judicial Branch | https://courts.mt.gov/ | judicial-branch |
| Justice | https://dojmt.gov/ | justice |
| Labor & Industry | https://dli.mt.gov/ | labor-industry |
| Legislative Branch | https://leg.mt.gov/ | legislative-branch |
| Livestock | https://liv.mt.gov/ | livestock |
| Lottery | https://www.montanalottery.com/en | lottery |
| Military Affairs | https://dma.mt.gov/ | military-affairs |
| Montana Board of Crime Control | https://mbcc.mt.gov/ | crime-control |
| Montana Public Employees Retirement Administration | https://mpera.mt.gov/ | mpera |
| MontanaWorks | https://montanaworks.gov | montanaworks |
| Natural Resources & Conservation | https://dnrc.mt.gov/ | natural-resources |
| Political Practices, Commissioner of | https://politicalpractices.mt.gov/ | political-practices |
| Public Defender, Office of the State | https://publicdefender.mt.gov/ | public-defender |
| Public Education, Board of | https://bpe.mt.gov/ | public-education |
| Public Health & Human Services | https://dphhs.mt.gov/ | health-human-services |
| Public Instruction, Office of | https://opi.mt.gov/ | public-instruction |
| Public Service Commission | https://psc.mt.gov/ | public-service-commission |
| Revenue | https://mtrevenue.gov/ | revenue |
| School for the Deaf & Blind | https://www.msdbmustangs.org/ | deaf-blind-school |
| Secretary of State | https://sosmt.gov/ | secretary-of-state |
| Securities & Insurance, Commissioner of | https://csimt.gov/ | securities-insurance |
| State Fund | https://www.montanastatefund.com/web | state-fund |
| State Library | https://msl.mt.gov/ | state-library |
| Teachers Retirement System | https://trs.mt.gov/ | teachers-retirement |
| Transportation | https://mdt.mt.gov/ | transportation |

---

## Secondary Data Sources (documented, not yet ingested)

These are additional sources that belong to an existing agency's corpus but are **not** standalone
agencies. They are intentionally written as prose (not a parseable table row) so the crawler does
**not** auto-crawl them via `--all`; ingestion happens deliberately once a viable extraction path
exists. When ingested, content goes in its own folder and is folded into the owning agency in the
knowledge graph via `resolve_agency` in `src/network/graph_builder.py`.

- **Commerce — Community Data (Tableau)** · base URL `https://tableau-ext.mt.gov/` · intended
  folder `commerce-tableau` · folds into agency **commerce**.
  Status: **DEFERRED**. This is a Tableau Server (vizportal) single-page app — the static
  HTML/PDF/DOCX crawler extracts nothing (the root is a ~1.3 KB JS shell with no links/text, and
  `robots.txt`/`sitemap.xml` 404). Content *is* reachable two ways, both needing a discovery step:
  (1) anonymous **PDF export** of a *known* view URL works
  (`/t/<SITE>/views/<Workbook>/<Sheet>.pdf`), but the commerce view URLs aren't embedded in any
  crawlable commerce page; (2) the Tableau **REST API** (`restApiVersion 3.25`) can list views but
  requires an authenticated token (401 anonymously). Revisit when a list of commerce view URLs or
  a Personal Access Token is available.

---

## Special Notes

### External Domains
Some agencies use domains outside of mt.gov:
- **Higher Education**: Uses `mus.edu` domain
- **Lottery**: Uses `montanalottery.com` domain
- **State Fund**: Uses `montanastatefund.com` domain
- **School for Deaf & Blind**: Uses `msdbmustangs.org` domain

### Duplicate Entries
Note: `Auditor` and `Securities & Insurance, Commissioner of` share the same domain (csimt.gov). The crawler will handle this automatically by using the first entry.

---

**Last Updated:** June 19, 2026
**Total Agencies:** 38
**Secondary data sources:** 1 documented, deferred (tableau-ext.mt.gov → commerce; see above)
