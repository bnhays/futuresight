export function renderMatchupHistory({
  apiUrl,
  deckId,
  currentDeck,
  currentVersionId,
  activeMatchupId,
  libraryDecks,
  matchupHistoryShowingAll,
  cloneDeck,
  getCurrentDeck,
  setCurrentDeck,
  setInitialDeck,
  setActiveMatchupId,
  setLibraryDecks,
  setMatchupHistoryShowingAll,
  renderDeck,
}) {
  const selectedLibraryDeck = (deckIdValue) => (libraryDecks || []).find((deck) => deck.id === deckIdValue);
  const selectedMatchup = () => (currentDeck?.matchups || []).find((matchup) => matchup.id === activeMatchupId) || null;

  async function loadLibraryDecks() {
    if (libraryDecks) return libraryDecks;

    const response = await fetch(`${apiUrl}/decks`);
    const decks = await response.json();
    if (!response.ok) {
      throw new Error(decks.detail || "Could not load deck library.");
    }

    const loadedDecks = Array.isArray(decks) ? decks : [];
    setLibraryDecks(loadedDecks);
    libraryDecks = loadedDecks;
    return loadedDecks;
  }

  function matchupDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function openMatchupEditor(matchupId) {
    const nextMatchupId = activeMatchupId === matchupId ? null : matchupId;
    setActiveMatchupId(nextMatchupId);
    renderDeck(getCurrentDeck().cards || []);
  }

  function matchupOutcomeClass(outcome) {
    const normalized = String(outcome || "").trim().toLowerCase();
    const scoreMatch = normalized.match(/^(\d+)\s*[-–]\s*(\d+)$/);
    if (scoreMatch) {
      const wins = Number(scoreMatch[1]);
      const losses = Number(scoreMatch[2]);
      if (wins > losses) return "matchup-result-victory";
      if (wins === losses) return "matchup-result-draw";
      return "matchup-result-loss";
    }
    if (["victory", "win", "won"].includes(normalized)) return "matchup-result-victory";
    if (["draw", "tie", "tied"].includes(normalized)) return "matchup-result-draw";
    if (["loss", "lose", "lost"].includes(normalized)) return "matchup-result-loss";
    return "";
  }

  function renderMatchupCard(matchup) {
    const card = document.createElement("article");
    card.className = "matchup-card";
    if (matchup.id === activeMatchupId) {
      card.classList.add("matchup-card-active");
    }
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Edit matchup against ${matchup.opponent_deck || "Unknown Deck"}`);
    card.addEventListener("click", () => openMatchupEditor(matchup.id));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openMatchupEditor(matchup.id);
      }
    });

    const opponent = document.createElement("h3");
    opponent.textContent = matchup.opponent_deck || "Unknown Deck";

    const outcomeClass = matchupOutcomeClass(matchup.outcome);
    if (outcomeClass) {
      const resultIndicator = document.createElement("span");
      resultIndicator.className = `matchup-result-indicator ${outcomeClass}`;
      if (matchup.opponent_deck_id) {
        resultIndicator.classList.add("matchup-result-with-deck-link");
      }
      resultIndicator.setAttribute("aria-label", matchup.outcome);
      resultIndicator.title = matchup.outcome;
      card.append(resultIndicator);
    }

    if (matchup.opponent_deck_id) {
      const deckLink = document.createElement("a");
      deckLink.className = "matchup-deck-link";
      deckLink.href = `/decks/view?id=${encodeURIComponent(matchup.opponent_deck_id)}`;
      deckLink.textContent = "";
      deckLink.setAttribute("aria-label", `Open ${matchup.opponent_deck || "opponent deck"} in library`);
      deckLink.addEventListener("click", (event) => {
        event.stopPropagation();
      });
      deckLink.addEventListener("keydown", (event) => {
        event.stopPropagation();
      });
      card.append(deckLink);
    }

    const tournament = document.createElement("p");
    tournament.className = "matchup-tournament";
    tournament.textContent = matchup.tournament_name || "Unknown Tournament";

    const meta = document.createElement("p");
    meta.className = "matchup-meta";

    const outcome = document.createElement("span");
    outcome.className = "matchup-outcome";
    outcome.textContent = matchup.outcome || "";

    const playedAt = document.createElement("span");
    playedAt.textContent = matchupDate(matchup.created_at);
    playedAt.hidden = !playedAt.textContent;

    meta.append(outcome, playedAt);
    card.append(opponent, tournament, meta);
    return card;
  }

  function matchupPayloadFromForm(form) {
    const formData = new FormData(form);
    const selectedDeckId = String(formData.get("opponent_deck_id") || "").trim();
    const selectedDeck = selectedLibraryDeck(selectedDeckId);
    return {
      opponent_deck: selectedDeck?.name || String(formData.get("opponent_deck") || "").trim(),
      opponent_deck_id: selectedDeckId || null,
      tournament_name: String(formData.get("tournament_name") || "").trim(),
      outcome: String(formData.get("outcome") || "").trim(),
    };
  }

  function renderMatchupTextField({ label, name, maxLength, value = "", placeholder = "" }) {
    const fieldLabel = document.createElement("label");
    const fieldText = document.createElement("span");
    fieldText.textContent = label;
    const input = document.createElement("input");
    input.name = name;
    input.type = "text";
    input.maxLength = maxLength;
    input.autocomplete = "off";
    input.value = value;
    input.placeholder = placeholder;
    fieldLabel.append(fieldText, input);
    return { fieldLabel, input };
  }

  function renderMatchupOpponentFields(matchup = {}) {
    const deckSelectLabel = document.createElement("label");
    const deckSelectText = document.createElement("span");
    deckSelectText.textContent = "Library Deck";
    const deckSelect = document.createElement("select");
    deckSelect.name = "opponent_deck_id";
    const customOption = document.createElement("option");
    customOption.value = "";
    customOption.textContent = "Custom opponent";
    deckSelect.append(customOption);
    (libraryDecks || [])
      .filter((deck) => deck.id !== deckId)
      .forEach((deck) => {
        const option = document.createElement("option");
        option.value = deck.id;
        option.textContent = deck.name || "Untitled Deck";
        option.selected = deck.id === matchup.opponent_deck_id;
        deckSelect.append(option);
      });
    deckSelectLabel.append(deckSelectText, deckSelect);

    const { fieldLabel: opponentLabel, input: opponentInput } = renderMatchupTextField({
      label: "Opponent Deck",
      name: "opponent_deck",
      maxLength: 80,
      value: matchup.opponent_deck || "",
    });

    deckSelect.addEventListener("change", () => {
      const selectedDeck = selectedLibraryDeck(deckSelect.value);
      if (selectedDeck) {
        opponentInput.value = selectedDeck.name || "Untitled Deck";
      }
    });
    opponentInput.addEventListener("input", () => {
      const selectedDeck = selectedLibraryDeck(deckSelect.value);
      if (selectedDeck && opponentInput.value !== (selectedDeck.name || "Untitled Deck")) {
        deckSelect.value = "";
      }
    });

    return { deckSelectLabel, opponentLabel, deckSelect };
  }

  function renderMatchupStatus() {
    const status = document.createElement("span");
    status.className = "matchup-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    return status;
  }

  async function saveEditedMatchup(event, form, status, submitButton) {
    event.preventDefault();
    if (!deckId || !currentVersionId() || !activeMatchupId) return;

    const payload = matchupPayloadFromForm(form);

    if (!payload.opponent_deck || !payload.tournament_name || !payload.outcome) {
      status.textContent = "Fill out all matchup fields.";
      return;
    }

    submitButton.disabled = true;
    status.textContent = "Saving...";

    try {
      const response = await fetch(
        `${apiUrl}/decks/${deckId}/versions/${currentVersionId()}/matchups/${activeMatchupId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const matchup = await response.json();
      if (!response.ok) {
        throw new Error(matchup.detail || "Could not update matchup.");
      }

      const updatedDeck = {
        ...getCurrentDeck(),
        matchups: (getCurrentDeck().matchups || []).map((item) => (
          item.id === matchup.id ? matchup : item
        )),
      };
      setCurrentDeck(updatedDeck);
      setInitialDeck(cloneDeck(updatedDeck));
      setActiveMatchupId(null);
      renderDeck(updatedDeck.cards || []);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Could not update matchup.";
      submitButton.disabled = false;
    }
  }

  async function deleteMatchup(status, deleteButton) {
    if (!deckId || !currentVersionId() || !activeMatchupId) return;
    const confirmed = window.confirm("Delete this matchup?");
    if (!confirmed) return;

    deleteButton.disabled = true;
    status.textContent = "Deleting...";

    try {
      const response = await fetch(
        `${apiUrl}/decks/${deckId}/versions/${currentVersionId()}/matchups/${activeMatchupId}`,
        { method: "DELETE" },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not delete matchup.");
      }

      const updatedDeck = {
        ...getCurrentDeck(),
        matchups: (getCurrentDeck().matchups || []).filter((matchup) => matchup.id !== activeMatchupId),
      };
      setCurrentDeck(updatedDeck);
      setInitialDeck(cloneDeck(updatedDeck));
      setActiveMatchupId(null);
      renderDeck(updatedDeck.cards || []);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Could not delete matchup.";
      deleteButton.disabled = false;
    }
  }

  function renderMatchupEditPanel(matchup) {
    const panel = document.createElement("div");
    panel.className = "matchup-edit-panel";

    const form = document.createElement("form");
    form.className = "matchup-form matchup-edit-form";

    const { deckSelectLabel, opponentLabel } = renderMatchupOpponentFields(matchup);
    const { fieldLabel: tournamentLabel } = renderMatchupTextField({
      label: "Tournament",
      name: "tournament_name",
      maxLength: 120,
      value: matchup.tournament_name || "",
    });
    const { fieldLabel: outcomeLabel } = renderMatchupTextField({
      label: "Outcome",
      name: "outcome",
      maxLength: 20,
      value: matchup.outcome || "",
      placeholder: "3-2",
    });

    const actions = document.createElement("div");
    actions.className = "matchup-form-actions matchup-edit-actions";

    const submitButton = document.createElement("button");
    submitButton.className = "action-button primary-button hollow-button";
    submitButton.type = "submit";
    submitButton.textContent = "Save";

    const cancelButton = document.createElement("button");
    cancelButton.className = "action-button muted hollow-button";
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", () => {
      setActiveMatchupId(null);
      renderDeck(getCurrentDeck().cards || []);
    });

    const deleteButton = document.createElement("button");
    deleteButton.className = "action-button danger-button hollow-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";

    const status = renderMatchupStatus();

    deleteButton.addEventListener("click", () => deleteMatchup(status, deleteButton));
    actions.append(submitButton, cancelButton, deleteButton, status);
    form.append(deckSelectLabel, opponentLabel, tournamentLabel, outcomeLabel, actions);
    form.addEventListener("submit", (event) => saveEditedMatchup(event, form, status, submitButton));

    panel.append(form);
    return panel;
  }

  function renderMatchupEditLoadingPanel() {
    const panel = document.createElement("div");
    panel.className = "matchup-edit-panel";
    const status = document.createElement("p");
    status.className = "matchup-status";
    status.textContent = "Loading deck library...";
    panel.append(status);
    loadLibraryDecks()
      .then(() => renderDeck(getCurrentDeck().cards || []))
      .catch((error) => {
        status.textContent = error instanceof Error ? error.message : "Could not load deck library.";
      });
    return panel;
  }

  async function saveMatchup(event, form, status, submitButton) {
    event.preventDefault();
    if (!deckId || !currentVersionId()) return;

    const payload = matchupPayloadFromForm(form);

    if (!payload.opponent_deck || !payload.tournament_name || !payload.outcome) {
      status.textContent = "Fill out all matchup fields.";
      return;
    }

    submitButton.disabled = true;
    status.textContent = "Saving...";

    try {
      const response = await fetch(
        `${apiUrl}/decks/${deckId}/versions/${currentVersionId()}/matchups`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const matchup = await response.json();
      if (!response.ok) {
        throw new Error(matchup.detail || "Could not save matchup.");
      }

      const updatedDeck = {
        ...getCurrentDeck(),
        matchups: [matchup, ...(getCurrentDeck().matchups || [])],
      };
      setCurrentDeck(updatedDeck);
      setInitialDeck(cloneDeck(updatedDeck));
      setMatchupHistoryShowingAll(false);
      renderDeck(updatedDeck.cards || []);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Could not save matchup.";
      submitButton.disabled = false;
    }
  }

  function renderMatchupForm(section, formContainer, logButton) {
    formContainer.innerHTML = "";
    formContainer.hidden = false;
    logButton.hidden = true;

    const form = document.createElement("form");
    form.className = "matchup-form matchup-log-form";

    const { deckSelectLabel, opponentLabel, deckSelect } = renderMatchupOpponentFields();
    const { fieldLabel: tournamentLabel } = renderMatchupTextField({
      label: "Tournament",
      name: "tournament_name",
      maxLength: 120,
    });
    const { fieldLabel: outcomeLabel } = renderMatchupTextField({
      label: "Outcome",
      name: "outcome",
      maxLength: 20,
      placeholder: "3-2",
    });

    const actions = document.createElement("div");
    actions.className = "matchup-form-actions";

    const submitButton = document.createElement("button");
    submitButton.className = "action-button primary-button hollow-button";
    submitButton.type = "submit";
    submitButton.textContent = "Save";

    const cancelButton = document.createElement("button");
    cancelButton.className = "action-button muted hollow-button";
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";

    const status = renderMatchupStatus();

    cancelButton.addEventListener("click", () => {
      formContainer.hidden = true;
      formContainer.innerHTML = "";
      logButton.hidden = false;
    });

    actions.append(submitButton, cancelButton, status);
    form.append(deckSelectLabel, opponentLabel, tournamentLabel, outcomeLabel, actions);
    form.addEventListener("submit", (event) => saveMatchup(event, form, status, submitButton));

    formContainer.append(form);
    section.append(formContainer);
    deckSelect.focus();
  }

  function renderMatchupFormLoading(section, formContainer, logButton) {
    formContainer.innerHTML = "";
    formContainer.hidden = false;
    logButton.hidden = true;

    const panel = document.createElement("div");
    panel.className = "matchup-edit-panel";

    const status = document.createElement("p");
    status.className = "matchup-status";
    status.textContent = "Loading deck library...";
    panel.append(status);

    formContainer.append(panel);
    section.append(formContainer);

    loadLibraryDecks()
      .then(() => renderMatchupForm(section, formContainer, logButton))
      .catch((error) => {
        status.textContent = error instanceof Error ? error.message : "Could not load deck library.";
        logButton.hidden = false;
      });
  }

  const section = document.createElement("section");
  section.className = "matchup-history-panel";

  const header = document.createElement("div");
  header.className = "panel-heading matchup-history-heading";

  const headingWrap = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = "Matchup History";
  const meta = document.createElement("p");
  meta.className = "matchup-history-meta";
  const matchups = currentDeck?.matchups || [];
  meta.textContent = `${matchups.length} logged ${matchups.length === 1 ? "matchup" : "matchups"} for this version`;
  headingWrap.append(heading, meta);

  const actions = document.createElement("div");
  actions.className = "deck-actions";

  const seeAllButton = document.createElement("button");
  seeAllButton.className = "action-button primary-button hollow-button compact-action";
  seeAllButton.type = "button";
  seeAllButton.textContent = matchupHistoryShowingAll ? "Show Recent" : "See All";
  seeAllButton.hidden = matchups.length <= 5;
  seeAllButton.addEventListener("click", () => {
    setMatchupHistoryShowingAll(!matchupHistoryShowingAll);
    renderDeck(getCurrentDeck().cards || []);
  });

  const logButton = document.createElement("button");
  logButton.className = "action-button success-button hollow-button compact-action";
  logButton.type = "button";
  logButton.textContent = "Log New";

  actions.append(seeAllButton, logButton);
  header.append(headingWrap, actions);
  section.append(header);

  const grid = document.createElement("div");
  grid.className = "matchup-grid";

  const visibleMatchups = matchupHistoryShowingAll ? matchups : matchups.slice(0, 5);
  if (visibleMatchups.length) {
    visibleMatchups.forEach((matchup) => {
      grid.append(renderMatchupCard(matchup));
    });
  }

  section.append(grid);

  const matchup = selectedMatchup();
  if (matchup && libraryDecks) {
    section.append(renderMatchupEditPanel(matchup));
  } else if (matchup) {
    section.append(renderMatchupEditLoadingPanel());
  }

  const formContainer = document.createElement("div");
  formContainer.className = "matchup-form-container";
  formContainer.hidden = true;

  logButton.addEventListener("click", () => {
    if (libraryDecks) {
      renderMatchupForm(section, formContainer, logButton);
      return;
    }
    renderMatchupFormLoading(section, formContainer, logButton);
  });

  section.append(formContainer);
  return section;
}
