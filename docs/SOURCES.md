# Source guide

A register by register account of what Romania publishes, with the questions
each source can and cannot answer.

Everything here is a primary source: the institution that creates the data
publishes it. Commercial aggregators repackage these same registers, add a
licence that forbids redistribution, and charge for the privilege. Going to
the source is cheaper, fresher and legally clean.

## ONRC, the National Trade Register Office

**Answers:** does this company exist, under what legal form, since when, at
what registered office, with which administrators, and is it still active.

**Identifiers:** the CUI (fiscal code) and the registration number in the form
`J40/3647/2021`, where `J40` encodes the county (40 is Bucharest), the middle
number is sequential within that county and year, and the last part is the
year.

**Limits:** shareholding and beneficial ownership are not generally available
in the free open data. If your analysis depends on who owns a company, budget
for that separately and do not assume the open data will get you there.

## ANAF, the tax authority

**Answers:** is this company VAT registered, is it on the inactive taxpayer
list, is it in the VAT on collection scheme, and what did it report in its
annual financial statements.

**The financial statements are the prize.** Turnover, total revenue, total
expenses, gross and net profit, employee count, assets and liabilities, per
company per year. This is the backbone of any segmentation by size.

**Limits:** statements lag. A financial year closes, filings are due months
later, and publication follows that. Plan for the most recent complete year
being one to two years behind the present. Micro entities file a reduced set,
so some fields are simply absent rather than zero. Never treat a missing
value as a zero: a company with no reported turnover has usually not filed,
not earned nothing.

## data.gov.ro, the national open data portal

**Answers:** give me the whole population at once.

Bulk CSV extracts of the trade register and tax data are published here. This
is how you get a starting universe without making a million requests.

**Limits:** republication is irregular and schemas drift between editions.
Column names change, encodings change, and a file that parsed last quarter
may not this quarter. Pin the edition you used, record its URL and download
date, and write your parser to fail loudly on an unexpected header rather
than silently mapping the wrong column.

## VIES, the EU VAT information exchange system

**Answers:** is this VAT number valid for intra community trade right now.

Queried live against the member state's own registry. Where the member state
consents, the registered name and address come back too.

**Limits:** "invalid" usually means "not VAT registered", which is an
ordinary state for a real company, not an error. Some member states return
`---` for name and address as a matter of policy. The service goes down, and
one country can be unavailable while the rest work.

**Use it for:** the evidence you keep to justify zero rating an intra
community supply. Store the response and the timestamp.

## EORI, via the EC DDS2 validator

**Answers:** is this economic operator registered to move goods across the EU
customs border.

**Why it matters commercially:** this is one of very few binary, officially
published signals that a small company actually trades internationally.
Companies do not register for an EORI number speculatively, they register
because they are about to ship something. For a Romanian company the number
is normally `RO` followed by the CUI.

**Limits:** valid means registered, not currently shipping. Name and address
appear only when the operator consented to publication. A blank name is a
consent decision, and treating it as a gap to be backfilled from elsewhere is
exactly the instinct to resist.

## SEAP / SICAP, public procurement

**Answers:** who sells to the Romanian state, what they sold, for how much,
and which institution bought it.

**Use it for:** a map of public buyers, competitor win rates, and contract
renewal timing.

**Limits:** buyer names are free text and vary between notices for the same
institution. Normalise before joining, and expect to maintain an alias table.
Awarded value and actual paid value are different things.

## BPI, the insolvency procedures bulletin

**Answers:** which companies have entered insolvency, reorganisation or
bankruptcy, and when.

**Use it for:** credit risk, and as a timing signal. A company in
reorganisation has a court supervised plan and a very different buying
posture from a healthy one.

**Limits:** publication lags the court decision, so absence from today's
bulletin is not evidence of health.

## Monitorul Oficial

**Answers:** statutory announcements that appear nowhere else.

**Limits:** unstructured text, expensive to parse, and rarely worth it unless
you have a specific question the structured registers cannot answer.

## A note on what is not here

There is no entry for any commercial company data website. Those sites
repackage the registers above under terms that prohibit redistribution.
Everything in this guide can be obtained from the institution that produced
it.
