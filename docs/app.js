const state = {
  products: [],
  query: "",
  sort: "sold_desc",
};

const rowsEl = document.querySelector("#productRows");
const totalCountEl = document.querySelector("#totalCount");
const searchInput = document.querySelector("#searchInput");
const sortSelect = document.querySelector("#sortSelect");

function numberValue(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatPrice(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `¥${number.toFixed(2).replace(/\.00$/, "")}`;
}

function formatSold(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return number.toLocaleString("zh-CN");
}

function formatTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sortedProducts(products) {
  const list = [...products];
  const sorters = {
    sold_desc: (a, b) => numberValue(b.sold_count, -1) - numberValue(a.sold_count, -1),
    sold_asc: (a, b) => numberValue(a.sold_count, Infinity) - numberValue(b.sold_count, Infinity),
    price_desc: (a, b) => numberValue(b.price, -1) - numberValue(a.price, -1),
    price_asc: (a, b) => numberValue(a.price, Infinity) - numberValue(b.price, Infinity),
    captured_desc: (a, b) => String(b.captured_at || "").localeCompare(String(a.captured_at || "")),
  };
  list.sort(sorters[state.sort] || sorters.sold_desc);
  return list;
}

function filteredProducts() {
  const query = state.query.trim().toLowerCase();
  const products = query
    ? state.products.filter((item) => String(item.product_name || "").toLowerCase().includes(query))
    : state.products;
  return sortedProducts(products).slice(0, 1000);
}

function render() {
  const products = filteredProducts();
  totalCountEl.textContent = String(products.length);

  if (!products.length) {
    rowsEl.innerHTML = '<tr><td colspan="6" class="empty">暂无匹配数据</td></tr>';
    return;
  }

  rowsEl.innerHTML = products
    .map((item) => {
      const link = escapeHtml(item.note_url || "");
      return `
        <tr>
          <td class="product-name">${escapeHtml(item.product_name || "-")}</td>
          <td>${formatPrice(item.price)}</td>
          <td class="sold">${formatSold(item.sold_count)}</td>
          <td>${escapeHtml(item.author_name || "-")}</td>
          <td><a href="${link}" target="_blank" rel="noopener noreferrer">打开笔记</a></td>
          <td>${escapeHtml(formatTime(item.captured_at))}</td>
        </tr>
      `;
    })
    .join("");
}

async function loadData() {
  try {
    const response = await fetch("./data/products.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.products = Array.isArray(data) ? data : [];
    render();
  } catch (error) {
    rowsEl.innerHTML = `<tr><td colspan="6" class="empty">数据加载失败：${escapeHtml(error.message)}</td></tr>`;
  }
}

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

sortSelect.addEventListener("change", (event) => {
  state.sort = event.target.value;
  render();
});

loadData();
