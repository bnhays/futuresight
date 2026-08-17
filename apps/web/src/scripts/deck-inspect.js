import { renderManaCost } from "./mana.js";

export function renderHoverPreview(card, previewContent) {
  if (!card || !previewContent) return;
  const data = card.card_data || {};
  previewContent.innerHTML = "";

  if (data.image_uri) {
    const image = document.createElement("img");
    image.src = data.image_uri;
    image.alt = data.name || card.name;
    previewContent.append(image);
  } else {
    const placeholder = document.createElement("div");
    placeholder.className = "deck-card-preview-empty";
    placeholder.textContent = data.name || card.name;
    previewContent.append(placeholder);
  }

  const typeText = document.createElement("p");
  typeText.textContent = data.type_line || "Unknown";
  previewContent.append(typeText);
}

export function showInspectCard({ card, inspectPanel, inspectContent, renderColorSquares }) {
  const data = card.card_data || {};
  inspectContent.innerHTML = "";

  const shell = document.createElement("article");
  shell.className = "inspect-card";

  const header = document.createElement("header");
  header.className = "inspect-card-header";

  const title = document.createElement("h2");
  title.textContent = data.name || card.name;
  header.append(title);

  const typeLine = document.createElement("p");
  typeLine.className = "inspect-card-type-line";
  typeLine.textContent = data.type_line || "Unknown";
  header.append(typeLine);
  shell.append(header);

  if (data.image_uri) {
    const media = document.createElement("div");
    media.className = "inspect-card-media";

    const image = document.createElement("img");
    image.src = data.image_uri;
    image.alt = data.name || card.name;
    media.append(image);
    shell.append(media);
  }

  const details = document.createElement("dl");
  details.className = "inspect-card-facts";

  function appendFact(label, value) {
    const item = document.createElement("div");
    item.className = "inspect-card-fact";

    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    if (value instanceof Node) {
      dd.append(value);
    } else {
      dd.textContent = String(value);
    }

    item.append(dt, dd);
    details.append(item);
  }

  [
    ["Quantity", card.quantity],
    ["Mana Value", data.cmc ?? ""],
  ].forEach(([label, value]) => appendFact(label, value));

  appendFact("Mana Cost", renderManaCost(data.mana_cost || ""));
  appendFact("Color Identity", renderColorSquares(data.color_identity || []));
  shell.append(details);

  if (data.oracle_text) {
    const oracleSection = document.createElement("section");
    oracleSection.className = "inspect-card-oracle";

    const oracleHeading = document.createElement("h3");
    oracleHeading.textContent = "Oracle Text";
    oracleSection.append(oracleHeading);

    const oracle = document.createElement("p");
    oracle.className = "oracle-text";
    oracle.textContent = data.oracle_text;
    oracleSection.append(oracle);
    shell.append(oracleSection);
  }

  if (data.scryfall_uri) {
    const link = document.createElement("a");
    link.className = "scryfall-link";
    link.href = data.scryfall_uri;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "View On Scryfall";
    shell.append(link);
  }

  inspectContent.append(shell);
  inspectPanel.hidden = false;
}
