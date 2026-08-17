# Requirements

## Functional Requirements
- The system should let a user create, view, and edit decks.
- The system should check whether a deck is legal for a selected format.
- The system should store deck versions as separate records so users can review changes over time.
- The system should let users name versions, add change notes, preview older versions, and restore a prior version as the latest deck state.
- The system should let users fork a prior version into a new deck.
- The system should let users log, edit, and delete basic matchup results for a specific deck version.
- The system should eventually support richer tournament results, matchup notes, and related observations.
- The system should show basic deck statistics such as mana curve, land color production, and card type breakdown.

## Data Requirements
- The system needs to store deck metadata, card lists, format information, and version history.
- The system needs to keep versioned deck records tied together with a shared deck identifier and version metadata such as version numbers, names, change notes, and timestamps.
- The system needs to track basic matchup result entries against individual deck versions.
- The system needs to support copying a selected deck version into a new deck when a user forks that version.
- The system should eventually track richer matchup results, tournament dates, notes, and opponent or archetype information.
- The system needs to retrieve card data from Scryfall and cache it locally to reduce repeated API calls.

## Non-Functional Requirements
- The project should be understandable to a new user and should not overload them with information.
- The project should provide clear descriptions of violations when a deck is illegal or when saved data changes.
- The project should be maintainable enough to support future features like deck branching and deeper analysis.
- The project should work reliably with locally cached card data to account for when external API access is slow or unavailable.

## Current Prototype Boundaries
- Full format legality enforcement remains planned.
- Side-by-side version comparison remains planned, although linear version history is now implemented.
- Matchup management is limited to opponent deck, optional linked library deck, tournament, outcome, and created date on a selected deck version.
- Deck statistics are limited to the current API-backed mana curve, land color production, and card type breakdown panels.

## Out of Scope for the First Version
- This version will not include simulated opening hands or full playtesting automation.
- This version will not include a full deck-branching tree interface.
- This version will not include advanced statistical analysis beyond the basic deck summaries listed above.
