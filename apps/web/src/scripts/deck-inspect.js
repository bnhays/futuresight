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

  const title = document.createElement("h2");
  title.textContent = data.name || card.name;
  inspectContent.append(title);

  if (data.image_uri) {
    const image = document.createElement("img");
    image.src = data.image_uri;
    image.alt = data.name || card.name;
    inspectContent.append(image);
  }

  const details = document.createElement("dl");
  [
    ["Quantity", card.quantity],
    ["Type", data.type_line || "Unknown"],
    ["Mana Value", data.cmc ?? ""],
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = String(value);
    details.append(dt, dd);
  });

  const manaDt = document.createElement("dt");
  manaDt.textContent = "Mana Cost";
  const manaDd = document.createElement("dd");
  manaDd.append(renderManaCost(data.mana_cost || ""));
  details.append(manaDt, manaDd);

  const colorDt = document.createElement("dt");
  colorDt.textContent = "Color Identity";
  const colorDd = document.createElement("dd");
  colorDd.append(renderColorSquares(data.color_identity || []));
  details.append(colorDt, colorDd);
  inspectContent.append(details);

  if (data.oracle_text) {
    const oracleHeading = document.createElement("h3");
    oracleHeading.textContent = "Oracle Text:";
    inspectContent.append(oracleHeading);

    const oracle = document.createElement("p");
    oracle.className = "oracle-text";
    oracle.textContent = data.oracle_text;
    inspectContent.append(oracle);
  }

  if (data.scryfall_uri) {
    const link = document.createElement("a");
    link.className = "scryfall-link";
    link.href = data.scryfall_uri;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "View On Scryfall";
    inspectContent.append(link);
  }

  inspectPanel.hidden = false;
}
