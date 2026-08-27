document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("navToggle");
  const nav = document.getElementById("mainNav");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", function () {
    const isOpen = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  // Đóng menu khi bấm 1 link (mobile)
  nav.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
});

// Hiện/ẩn ô "Nhập tên (Khác)" khi chọn "Khác..." ở dropdown Người nhập
document.addEventListener("DOMContentLoaded", function () {
  const select = document.getElementById("nguoiNhapSelect");
  const wrap = document.getElementById("nguoiNhapKhacWrap");
  if (!select || !wrap) return;

  function syncKhac() {
    const isKhac = select.value === "Khác";
    wrap.hidden = !isKhac;
    const input = wrap.querySelector("input");
    if (input) input.required = isKhac;
  }

  select.addEventListener("change", syncKhac);
  syncKhac(); // đồng bộ ngay khi tải trang (VD form bị trả lại do lỗi)
});

document.addEventListener("DOMContentLoaded", function () {
  const copyButton = document.getElementById("copyTextButton");
  const copyText = document.getElementById("copyText");
  const copyStatus = document.getElementById("copyStatus");
  if (!copyButton || !copyText) return;

  copyButton.addEventListener("click", async function () {
    try {
      await navigator.clipboard.writeText(copyText.value);
    } catch (error) {
      copyText.focus();
      copyText.select();
      document.execCommand("copy");
    }
    copyStatus.textContent = "Đã sao chép nội dung.";
    copyButton.textContent = "Đã sao chép";
  });
  });

  document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("recordSearch");
    const recordIdInput = document.getElementById("recordId");
    const results = document.getElementById("recordResults");
    const selectedRecord = document.getElementById("selectedRecord");
    const noResults = document.getElementById("noSearchResults");
    if (!searchInput || !recordIdInput || !results) return;

    const resultButtons = Array.from(results.querySelectorAll(".search-result"));
    const normaliseSearchText = function (value) {
      return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    };

    function filterResults() {
      const query = normaliseSearchText(searchInput.value.trim());
      let visibleCount = 0;
      resultButtons.forEach(function (button) {
        const matches = !query || normaliseSearchText(button.dataset.search).includes(query);
        button.hidden = !matches;
        if (matches) visibleCount += 1;
      });
      if (noResults) noResults.hidden = visibleCount !== 0;
    }

    resultButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        recordIdInput.value = button.dataset.recordId || "";
        searchInput.value = button.querySelector("strong").textContent;
        selectedRecord.textContent = "Đã chọn mã: " + recordIdInput.value;
        selectedRecord.hidden = !recordIdInput.value;
        results.classList.remove("is-open");
        resultButtons.forEach(function (item) { item.classList.remove("is-selected"); });
        button.classList.add("is-selected");
    });
    });

    searchInput.addEventListener("input", function () {
      recordIdInput.value = "";
      if (selectedRecord) selectedRecord.hidden = true;
      results.classList.toggle("is-open", searchInput.value.trim().length > 0);
      filterResults();
  });
    filterResults();
});
