---
phase: 04-activation-and-dashboards
plan: "02"
subsystem: api
tags: [analytics, posthog, onboarding, fastapi, react-query]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: analytics service (get_analytics_service, capture, group_identify)
  - phase: 01-foundation
    provides: analytics_constants with ONBOARDING_COMPLETED event name
provides:
  - POST /api/onboarding endpoint that fires ONBOARDING_COMPLETED analytics event
  - Consent-gated onboarding analytics capture with role, org_size, use_case properties
  - Org group_identify call associating onboarding_completed_at timestamp
  - Frontend hook calling real API endpoint and using redirect_url from response
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Inline enterprise imports inside try/except for OSS safety"
    - "Analytics wrapped in broad try/except so it never breaks user flow"
    - "Consent checked via user_obj.user_consents_to_analytics before capture"

key-files:
  created:
    - enterprise/server/routes/onboarding.py
  modified:
    - enterprise/saas_server.py
    - frontend/src/hooks/mutation/use-submit-onboarding.ts

key-decisions:
  - "No DB persistence of onboarding responses — analytics event IS the persistence; DB model deferred if needed"
  - "redirect_url hardcoded to '/' on backend; frontend reads from response for future flexibility"
  - "group_identify fires only when org_id_str is present — personal-org users still get user-level event"

patterns-established:
  - "Onboarding endpoint pattern: accept selections dict, map step keys to event properties, fire capture + group_identify"

requirements-completed: [ACTV-03]

# Metrics
duration: 3min
completed: 2026-03-03
---

# Phase 04 Plan 02: Onboarding Submission Endpoint Summary

**POST /api/onboarding endpoint fires ONBOARDING_COMPLETED PostHog event with role, org_size, and use_case from user selections; frontend hook wired from TODO stub to real API call**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-03T00:40:00Z
- **Completed:** 2026-03-03T00:43:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created enterprise/server/routes/onboarding.py with POST /api/onboarding endpoint
- Endpoint fires ONBOARDING_COMPLETED event (ACTV-03) with role, org_size, use_case mapped from step selections
- Endpoint fires group_identify to associate onboarding_completed_at timestamp with org group
- Analytics is consent-gated and wrapped in try/except — never blocks the user flow
- Registered onboarding_router in enterprise/saas_server.py
- Replaced frontend TODO stub with real openHands.post call reading redirect_url from API response

## Task Commits

Each task was committed atomically:

1. **Task 1: Create backend onboarding endpoint with analytics capture** - `c44e09c31` (feat)
2. **Task 2: Wire frontend onboarding hook to real API endpoint** - `73543d2ff` (feat)

## Files Created/Modified
- `enterprise/server/routes/onboarding.py` - New POST /api/onboarding route with ONBOARDING_COMPLETED analytics capture
- `enterprise/saas_server.py` - Added onboarding_router import and include_router registration
- `frontend/src/hooks/mutation/use-submit-onboarding.ts` - Replaced TODO stub with real API call via openHands.post

## Decisions Made
- No DB persistence of onboarding responses added — the analytics event in PostHog IS the persistence for ACTV-03 scope. A DB model can be added later if product wants queryable data outside PostHog.
- redirect_url is hardcoded to '/' on the backend for now; the frontend reads it from the response, so the backend can evolve this later without frontend changes.
- group_identify fires only when org_id_str is non-null. Personal-org users still receive the user-level ONBOARDING_COMPLETED event.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ACTV-03 onboarding completed event is now in place
- Ready to continue with remaining activation and dashboard plans in phase 04

---
*Phase: 04-activation-and-dashboards*
*Completed: 2026-03-03*
