export const API_URL = import.meta.env.PUBLIC_API_URL || "http://localhost:8000";

export function formatDeckFormat(format) {
  if (!format) return "";
  return format.charAt(0).toUpperCase() + format.slice(1);
}

export function formatShortDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function formatFullDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function renderColorSquares(colors, options = {}) {
  const { order = null, labels = {} } = options;
  const wrapper = document.createElement("span");
  wrapper.className = "color-squares";

  const visibleColors = order
    ? order.filter((color) => colors?.includes(color))
    : (colors || []);

  visibleColors.forEach((color) => {
    const square = document.createElement("span");
    square.className = `color-square color-${String(color).toLowerCase()}`;
    if (labels[color]) {
      square.title = labels[color];
    }
    wrapper.append(square);
  });

  return wrapper;
}
