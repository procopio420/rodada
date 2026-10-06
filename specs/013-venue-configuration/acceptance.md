# Acceptance — Spec 013

## Typed configuration

**Given** a manager opens Venue settings  
**When** configuration is loaded  
**Then** settings are grouped into typed domain sections rather than returned as an unrestricted key/value dictionary.

## Permission denial

**Given** MANAGER lacks owner-only provider credential capability  
**When** they submit provider secret configuration directly  
**Then** backend rejects it and existing binding is unchanged.

## Station safe-change blocker

**Given** KITCHEN has active queued OrderItems  
**When** manager tries to deactivate the only KITCHEN station  
**Then** preview/apply returns the active blockers and does not orphan those items.

## Service charge versioning

**Given** open Tabs captured a 10% service-charge policy  
**When** owner changes default to 12%  
**Then** new policy becomes effective according to configured boundary and existing Tabs are not silently repriced.

## Guest emergency block

**Given** guest ordering is active  
**When** manager enables the global guest-ordering block  
**Then** new guest mutations are rejected immediately, staff ordering remains available and confirmed guest Orders remain intact.

## Business date cutoff

**Given** cutoff changes from 04:00 to 06:00 effective next business date  
**When** historical reports are queried  
**Then** prior business_date assignments remain unchanged.

## Provider boundary

**Given** an active payment provider binding  
**When** Gerência reads it  
**Then** it sees provider status and normalized capabilities but never the raw secret.

## Pending payment blocker

**Given** a provider has Payment in CONFIRMATION_PENDING  
**When** owner attempts to disable the binding  
**Then** change is blocked or staged until reconciliation according to provider policy; the pending Payment is not orphaned.

## Concurrent configuration edit

**Given** two managers edit the same alert threshold version  
**When** both save  
**Then** one succeeds and the stale editor receives current state rather than overwriting silently.

## Table history safety

**Given** a Table has historical occupancies  
**When** manager wants it removed from service  
**Then** it is archived/out-of-service through domain rules; history and QR identity are not destructively deleted.

## Operating hours non-enforcement

**Given** configured public operating hours have ended  
**When** authorized staff needs to close a Tab  
**Then** P0 does not block the POS solely because the schedule ended.

## Degraded state

**Given** Gerência is offline/stale  
**When** manager edits settings locally  
**Then** UI does not claim the change is active until server confirms it.

## Audit

**Given** cutoff, service policy, station and provider binding changes  
**When** configuration history is inspected  
**Then** actor, old/new typed state, applied/effective time and reason where required are present, with secrets redacted.
