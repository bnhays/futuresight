export function groupBySection(cards) {
  return cards.reduce((groups, card) => {
    const section = card.section || "mainboard";
    groups[section] = groups[section] || [];
    groups[section].push(card);
    return groups;
  }, {});
}

export function deckToText(cards) {
  const groups = groupBySection(cards || []);
  const lines = [];

  (groups.mainboard || []).forEach((card) => {
    lines.push(`${card.quantity} ${card.name}`);
  });

  if ((groups.sideboard || []).length) {
    if (lines.length) lines.push("");
    lines.push("Sideboard");
    groups.sideboard.forEach((card) => {
      lines.push(`${card.quantity} ${card.name}`);
    });
  }

  return lines.join("\n");
}

export function cloneDeck(deck) {
  return JSON.parse(JSON.stringify(deck));
}

export function normalizeText(value) {
  return String(value || "").trim();
}
