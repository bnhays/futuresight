export function getListType(typeLine) {
  const cardTypes = String(typeLine || "").split("-")[0] || "";
  const priorities = ["Creature", "Land", "Planeswalker", "Artifact", "Enchantment", "Instant", "Sorcery"];
  return priorities.find((type) => new RegExp(`\\b${type}\\b`, "i").test(cardTypes)) || typeLine || "";
}

export function renderManaCurve(curve) {
  const buckets = Array.isArray(curve) ? curve : [];
  const maxCount = Math.max(1, ...buckets.map((bucket) => bucket.count));

  const panel = document.createElement("section");
  panel.className = "mana-curve-panel";
  panel.setAttribute("aria-labelledby", "mana-curve-heading");

  const heading = document.createElement("h2");
  heading.id = "mana-curve-heading";
  heading.textContent = "Mana Curve";
  panel.append(heading);

  const bars = document.createElement("div");
  bars.className = "mana-curve-bars";

  buckets.forEach((bucket) => {
    const bar = document.createElement("div");
    bar.className = "mana-curve-bar";

    const count = document.createElement("span");
    count.className = "mana-curve-count";
    count.textContent = String(bucket.count);

    const fill = document.createElement("span");
    fill.className = "mana-curve-fill";
    fill.style.height = `${Math.max(0.12, bucket.count / maxCount) * 100}%`;

    const label = document.createElement("span");
    label.className = "mana-curve-label";
    label.textContent = bucket.label;

    bar.append(count, fill, label);
    bars.append(bar);
  });

  panel.append(bars);
  return panel;
}

export function renderLandColorProduction(production) {
  const colors = Array.isArray(production) ? production : [];

  const panel = document.createElement("section");
  panel.className = "land-colors-panel";
  panel.setAttribute("aria-labelledby", "land-colors-heading");

  const heading = document.createElement("h2");
  heading.id = "land-colors-heading";
  heading.textContent = "Land Colors";
  panel.append(heading);

  const bars = document.createElement("div");
  bars.className = "land-color-bars";

  colors.forEach((item) => {
    const row = document.createElement("div");
    row.className = "land-color-row";

    const label = document.createElement("span");
    label.className = "land-color-label";
    label.textContent = item.label;

    const track = document.createElement("span");
    track.className = "land-color-track";
    track.setAttribute("aria-label", `${item.label}: ${item.percentage}% of lands`);

    const fill = document.createElement("span");
    fill.className = `land-color-fill color-${item.color.toLowerCase()}`;
    fill.style.width = `${item.percentage}%`;
    track.append(fill);

    const value = document.createElement("span");
    value.className = "land-color-value";
    value.textContent = `${item.percentage}%`;

    row.append(label, track, value);
    bars.append(row);
  });

  panel.append(bars);
  return panel;
}
