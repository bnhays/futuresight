function manaSymbolClass(value) {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\//g, "");

  const aliases = {
    "∞": "infinity",
    "½": "half",
  };

  return aliases[normalized] || normalized;
}

function manaColorClass(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const colorClasses = {
    w: "white",
    u: "blue",
    b: "black",
    r: "red",
    g: "green",
    c: "colorless",
    s: "snow",
  };

  return colorClasses[normalized] || "generic";
}

function renderSpecialManaSymbol(value) {
  const normalized = String(value || "").trim();
  const upperValue = normalized.toUpperCase();
  const symbolEl = document.createElement("span");
  symbolEl.className = "mana-symbol mana-symbol-custom";
  symbolEl.setAttribute("role", "img");
  symbolEl.setAttribute("aria-label", normalized);
  symbolEl.title = normalized;

  if (upperValue === "S") {
    symbolEl.classList.add("mana-symbol-snow");
    const snowIcon = document.createElement("i");
    snowIcon.className = "mana-symbol-mark ms ms-s";
    symbolEl.append(snowIcon);
    return symbolEl;
  }

  const parts = normalized.split("/");
  const isPhyrexian = parts.at(-1)?.toUpperCase() === "P";

  if (isPhyrexian && parts.length === 2) {
    const colorClass = manaColorClass(parts[0]);
    symbolEl.classList.add(
      "mana-symbol-phyrexian",
      "mana-symbol-solid",
      `mana-solid-${colorClass}`,
    );

    const phyrexianIcon = document.createElement("i");
    phyrexianIcon.className = "mana-symbol-mark mana-symbol-phyrexian-mark ms ms-p";
    symbolEl.append(phyrexianIcon);
    return symbolEl;
  }

  if (isPhyrexian && parts.length === 3) {
    const leftClass = manaColorClass(parts[0]);
    const rightClass = manaColorClass(parts[1]);
    symbolEl.classList.add(
      "mana-symbol-phyrexian",
      "mana-symbol-phyrexian-dual",
      `mana-split-left-${leftClass}`,
      `mana-split-right-${rightClass}`,
    );

    const phyrexianIcon = document.createElement("i");
    phyrexianIcon.className = "mana-symbol-mark mana-symbol-phyrexian-mark ms ms-p";
    symbolEl.append(phyrexianIcon);
    return symbolEl;
  }

  if (parts.length !== 2) return null;

  const [left, right] = parts;
  const leftClass = manaColorClass(left);
  const rightClass = manaColorClass(right);
  symbolEl.classList.add(
    "mana-symbol-hybrid",
    `mana-split-left-${leftClass}`,
    `mana-split-right-${rightClass}`,
  );

  const leftMark = document.createElement("span");
  leftMark.className = "mana-symbol-half mana-symbol-half-left";
  if (/^\d+$/.test(left)) {
    leftMark.textContent = left;
  } else {
    const leftIcon = document.createElement("i");
    leftIcon.className = `mana-symbol-mark ms ms-${manaSymbolClass(left)}`;
    leftMark.append(leftIcon);
  }

  const rightMark = document.createElement("span");
  rightMark.className = "mana-symbol-half mana-symbol-half-right";
  if (/^\d+$/.test(right)) {
    rightMark.textContent = right;
  } else {
    const rightIcon = document.createElement("i");
    rightIcon.className = `mana-symbol-mark ms ms-${manaSymbolClass(right)}`;
    rightMark.append(rightIcon);
  }

  symbolEl.append(leftMark, rightMark);
  return symbolEl;
}

export function renderManaCost(manaCost) {
  const wrapper = document.createElement("span");
  wrapper.className = "mana-cost";
  const symbols = String(manaCost || "").match(/\{[^}]+\}/g) || [];

  if (!symbols.length && manaCost) {
    wrapper.textContent = manaCost;
    return wrapper;
  }

  symbols.forEach((symbol) => {
    const value = symbol.replace(/[{}]/g, "");
    const specialSymbol = renderSpecialManaSymbol(value);
    if (specialSymbol) {
      wrapper.append(specialSymbol);
      return;
    }

    const symbolEl = document.createElement("i");
    symbolEl.className = `mana-symbol ms ms-cost ms-${manaSymbolClass(value)}`;
    symbolEl.setAttribute("role", "img");
    symbolEl.setAttribute("aria-label", value);
    symbolEl.title = value;
    wrapper.append(symbolEl);
  });

  return wrapper;
}
