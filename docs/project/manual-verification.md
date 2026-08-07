# Manual Verification

## Actions Performed

Manual verification was performed against the Docker-based application build.

- Built and ran the application with Docker.
- Imported several decklists with varying card types and structures.
- Reviewed imported deck detail pages.
- Edited deck details, including deck metadata and decklist content.
- Saved deck edits and entered prompted change notes.
- Opened the Versions page and selected older deck versions from the version list.
- Edited version names and change notes from the Versions page.
- Confirmed historical version detail pages were preview-only.
- Tried saving an unchanged edit form.
- Restored an older version and confirmed it appeared as the newest version.
- Reviewed mana curve and land-produced-color panels on deck detail pages.
- Logged basic matchup results for selected deck versions.
- Used the matchup history recent/all toggle after multiple entries were present.
- Used quick card-quantity update controls from the deck detail view.
- Deleted saved decks.
- Checked various potential error states, including missing or invalid input and unavailable deck data.

## Expected Results

- The Docker build should start the Astro client, FastAPI server, and MongoDB services.
- The deck import form should accept valid decklists and create saved decks.
- Imported decks should show card names, quantities, sections, card details, and available Scryfall data.
- Deck metadata and decklist edits should save and appear after returning to the deck detail view.
- Each changed deck edit should append a new automatically numbered version while preserving previous decklists.
- Saving an unchanged edit form should not create a new version.
- The deck detail Versions button should open a version list page.
- Version names and change notes should save from the version list without changing deck contents.
- Version list items should open preview-only deck detail pages.
- Historical preview pages should not allow editing or quick quantity updates.
- Restoring an older version should duplicate it as a new latest version.
- Deck detail pages should show basic client-side deck analysis panels for mana curve and land-produced-color distribution.
- Matchup history should show entries logged for the selected deck version.
- The matchup form should reject blank fields and save entries with opponent deck, tournament, outcome, and date.
- Quick quantity updates should mark the deck as changed and allow the updated decklist to be saved.
- Deleted decks should be removed from the saved deck list and should no longer open in the detail view.
- Error states should provide a visible message or safe empty state instead of breaking the page.

## Observed Results

- The application built and ran through Docker.
- Multiple decklists of varying types were imported successfully.
- Deck detail pages loaded and displayed saved deck information.
- Deck metadata editing and quick quantity updates worked as expected for the tested flows.
- Version history, version metadata editing, historical preview, and restore flows worked as expected for the tested flows.
- Basic matchup logging and matchup history display worked as expected for the tested flows.
- Mana curve and land-produced-color panels appeared on deck detail pages.
- Deck deletion worked as expected for the tested flows.
- Error and empty states were checked and did not prevent continued use of the prototype.

## Issues Found

- Certain card types that do not have a clean exact mana cost do not render anything for their mana value.
- Some unwanted row wrapping occurs when there is too much information to fit cleanly in one card table row.

## Engineering Conclusion

The prototype satisfies the core project goal for this update: users can build, run, import, inspect, edit, update, and delete decks through the full stack. The remaining issues are visual rendering and layout polish rather than blockers for the primary deck-management workflow.

Future work should improve edge-case mana rendering, tighten dense row layout behavior, and continue the planned implementation of deferred features such as legality checks, backend statistics, richer matchup and tournament tracking, and version comparison.
