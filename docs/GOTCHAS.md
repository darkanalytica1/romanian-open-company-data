# Gotchas

Failure modes that produce no error message, which is what makes them
expensive. Ordered roughly by how much damage they do.

## 1. The cedilla that is not a comma below

Romanian s and t with a comma below are U+0219 and U+021B. The Turkish
cedilla forms, U+015F and U+0163, look nearly identical and were used by
Romanian software for years because early code pages did not distinguish
them.

Public registers contain both. Sometimes in the same file. Sometimes in the
same record.

If your normaliser folds only one pair, `Ţesătoria Şerban` and `Țesătoria
Șerban` are different strings, your join silently misses, and your match rate
looks like a data availability problem rather than an encoding bug. Fold both
pairs, then normalise to NFKD and strip remaining combining marks to catch
anything else.

`rocompany.names.fold_diacritics` does this.

## 2. Treating a service error as a negative answer

VIES and the EORI validator both go down, time out, and return transient
errors. If your pipeline records a timeout as `invalid`, you will eventually
mark a real, valid, paying customer as deregistered and act on it.

Model three states, not two: valid, invalid, and unknown. Only a clear
response from the service moves a record out of unknown. Retry unknowns on a
schedule.

## 3. Missing is not zero

A company with no turnover in the financial statements has almost always not
filed yet, or files a reduced micro entity set. It has not earned nothing.

Coercing nulls to zero at load time destroys the distinction permanently and
produces segment averages that are quietly wrong. Keep the null, and decide
how to treat it at analysis time, per question.

## 4. The checksum that passes by accident

The CUI check digit rejects about ten of every eleven arbitrary numbers,
which makes it an excellent cheap filter. It is not proof of existence. The
postcode `010101` validates. So do plenty of order references and short
account numbers.

Validate locally to avoid wasting network calls, then confirm survivors
against a register before you treat them as companies.

## 5. Merging two companies that share a trading name

`ALFA COM SRL` and `ALFA COM SA` normalise to the same core name and are two
different legal entities, with different owners, different liabilities and
possibly different tax status.

Strip the legal form for comparison, but keep it, and treat a form mismatch
as evidence against a match rather than noise to be ignored. Better still,
never decide a match on name alone: require a second independent signal, a
shared CUI, a shared registration number, or the name verified on the
company's own website.

## 6. The declared activity code is a historical artefact

A company declares its principal CAEN code at registration and has no reason
ever to update it. A firm registered in 2004 as a wholesaler may now be a
software company.

The code is a strong prior for segmentation and a bad ground truth. Sanity
check it against revenue, headcount, and what the company says about itself.
Where the three disagree, the register is usually the one that is stale.

## 7. Spreadsheets that eat leading zeros and add decimal points

CAEN code `0111` arrives as `111`. Fiscal code `43825150` arrives as
`43825150.0`. Both are Excel doing what Excel does.

Handle both at the edge of your system: strip a trailing `.0`, left pad
activity codes to four digits. `rocompany.caen.normalise` and
`rocompany.cui.normalise` do this.

## 8. Nomenclature gaps

NACE Rev. 2 has no division 34. A validator that assumes divisions run
continuously from 01 to 99 will accept `3400` as an activity code and you
will carry a phantom segment through your whole analysis.

Encode the actual section boundaries, and reject codes that fall in a gap.

## 9. Hardcoding a nomenclature that gets revised

Activity code labels, country IBAN lengths and procurement classification
trees all change. Baking several hundred labels into source code guarantees
they are wrong within a few years, and the wrongness is invisible.

Pin the structure in code, load the labels from a file you can refresh, and
record where and when you downloaded it.

## 10. Bulk querying a service built for single lookups

The official validators are free and public because they are intended for one
at a time verification. Treating one as a bulk feed gets your address blocked,
and there is no support desk to unblock you.

Rate limit, back off, cache aggressively, and re validate on a TTL rather
than on every run. Registration status changes rarely: quarterly is usually
enough for valid records, sooner for ones that came back negative.
