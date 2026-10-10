# Acceptance — Spec 016

## Staff Web pilot capture — 2026-10-10
- [ ] Active occupancy shows unknown without default 1; optional capture does not block other operations.
- [ ] 1–8/manual selector posts a positive integer, read version and stable key; canonical response alone changes displayed count.
- [ ] Ambiguous retry preserves original count/version/reason/key and freezes editing.
- [ ] Version conflict refreshes canonical count and asks for deliberate resubmission; no automatic overwrite.
- [ ] Android active-occupancy chooser follows the same unknown/version/retry rules; scrollable controls remain reachable with keyboard/font enlargement.

## Unknown default

**Given** an existing or new occupancy with no party-size entry  
**When** it is displayed  
**Then** covers are UNKNOWN/“—”, not 0 or 1, and ordering is not blocked.

## Multiple Tabs

**Given** one TableOccupancy with three Tabs and party size 6  
**When** cover analytics run  
**Then** the visit contributes 6 covers, not 18 and not 3.

## Staff capture

**Given** an active occupancy with unknown covers  
**When** authorized staff records 5  
**Then** current party size becomes 5 with STAFF provenance and no financial state changes.

## Guest capture

**Given** valid GuestSession starts a DIRECT occupancy  
**When** guest records 4 people  
**Then** current count is 4 with GUEST provenance and staff can see/correct it.

## Concurrency

**Given** guest and staff both loaded version 2  
**When** guest writes 4 and staff writes 5 concurrently  
**Then** one commit wins and the stale request receives current value/provenance; no silent last-write overwrite.

## Correction

**Given** active count was 4 but staff confirms actual party is 5  
**When** corrected  
**Then** a new observation supersedes 4; old observation remains in history.

## Post-release correction

**Given** occupancy released with count 5  
**When** manager later corrects factual count to 6 with reason  
**Then** prior release/observation remain auditably visible and rebuilt analytics may use 6.

## Tab without table

**Given** a standing-party Tab never associated to TableOccupancy  
**When** staff explicitly records Tab party size 3  
**Then** it may contribute 3 covers to eligible non-table analytics.

## Later join occupancy

**Given** that Tab with count 3 later joins an occupancy whose covers are 7  
**When** venue cover analytics run  
**Then** occupancy count 7 is canonical for that physical visit and the Tab count is not added.

## Revenue per cover

**Given** two known-cover visits with net eligible revenue 10000/4 covers and 6000/2 covers  
**When** period revenue per cover is computed  
**Then** result is 16000 / 6, not the unweighted average of the two visit ratios.

## Missing-data honesty

**Given** half of visits have UNKNOWN covers  
**When** Gerência shows revenue per cover  
**Then** it also shows known/unknown visit counts or coverage percentage and does not imply full-population precision.

## Permission denial

**Given** a guest session for another occupancy  
**When** it submits party size for this occupancy  
**Then** backend rejects it.

## Offline

**Given** API is offline  
**When** staff changes local party-size draft  
**Then** it is not displayed as canonical until server replay succeeds.

## Audit

**Given** a manager post-release correction  
**When** history is inspected  
**Then** old/new count, actor, source, reason and timestamps are recoverable.
