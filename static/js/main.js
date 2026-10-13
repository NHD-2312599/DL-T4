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

/* ---------- Celebration micro-interaction ---------- */
window.Dlt4Celebrate = function (options) {
  options = options || {};
  var message = options.message || 'Tuyệt vời!';
  var colors = ['#C1442C', '#6E8F4C', '#D8A23B', '#9E3320', '#8AA969', '#E8C99A'];

  var layer = document.createElement('div');
  layer.className = 'dlt4-confetti-layer';
  layer.setAttribute('aria-hidden', 'true');
  var count = 36;
  for (var i = 0; i < count; i++) {
    var piece = document.createElement('span');
    piece.className = 'dlt4-confetti-piece';
    piece.style.left = Math.random() * 100 + '%';
    piece.style.background = colors[i % colors.length];
    piece.style.animationDuration = (1.4 + Math.random() * 1.4) + 's';
    piece.style.animationDelay = (Math.random() * 0.35) + 's';
    piece.style.width = (6 + Math.random() * 6) + 'px';
    piece.style.height = (8 + Math.random() * 8) + 'px';
    piece.style.opacity = String(0.75 + Math.random() * 0.25);
    layer.appendChild(piece);
  }
  document.body.appendChild(layer);

  var toast = document.createElement('div');
  toast.className = 'dlt4-celebrate-toast';
  toast.setAttribute('role', 'status');
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(function () {
    toast.classList.add('is-visible');
  });

  setTimeout(function () {
    toast.classList.remove('is-visible');
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
      if (layer.parentNode) layer.parentNode.removeChild(layer);
    }, 400);
  }, 2800);
};

/* ---------- Add to Home Screen (Android + iOS) ---------- */
window.Dlt4InstallGuide = function () {
  var androidBlock = document.getElementById("installAndroid");
  var iosBlock = document.getElementById("installIos");
  var genericBlock = document.getElementById("installGeneric");
  var installBtn = document.getElementById("installAppBtn");
  var installDone = document.getElementById("installDone");
  if (!androidBlock && !iosBlock && !genericBlock) return;

  var ua = navigator.userAgent || "";
  var isIos = /iphone|ipad|ipod/i.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var isAndroid = /android/i.test(ua);
  var isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  function show(el) {
    if (el) el.hidden = false;
  }
  function hide(el) {
    if (el) el.hidden = true;
  }

  if (isStandalone) {
    hide(androidBlock);
    hide(iosBlock);
    hide(genericBlock);
    show(installDone);
    return;
  }

  if (isIos) {
    hide(androidBlock);
    hide(genericBlock);
    show(iosBlock);
  } else if (isAndroid) {
    hide(iosBlock);
    // Prefer native install button when beforeinstallprompt fires; else show generic Android steps
    hide(androidBlock);
    show(genericBlock);
    // Pre-select Android tab
    var tabs = document.querySelectorAll(".install-tab");
    tabs.forEach(function (t) {
      t.classList.toggle("is-active", t.getAttribute("data-platform") === "android");
    });
    document.querySelectorAll(".install-panel").forEach(function (p) {
      p.hidden = p.getAttribute("data-panel") !== "android";
    });
  } else {
    hide(androidBlock);
    hide(iosBlock);
    show(genericBlock);
  }

  // Platform tabs (generic)
  document.querySelectorAll(".install-tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      var platform = tab.getAttribute("data-platform");
      document.querySelectorAll(".install-tab").forEach(function (t) {
        t.classList.toggle("is-active", t === tab);
      });
      document.querySelectorAll(".install-panel").forEach(function (p) {
        p.hidden = p.getAttribute("data-panel") !== platform;
      });
    });
  });

  // Android native install prompt
  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (isAndroid || !isIos) {
      hide(genericBlock);
      hide(iosBlock);
      show(androidBlock);
    }
  });

  if (installBtn) {
    installBtn.addEventListener("click", function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (choice) {
        deferredPrompt = null;
        if (choice && choice.outcome === "accepted") {
          hide(androidBlock);
          show(installDone);
        }
      });
    });
  }

  window.addEventListener("appinstalled", function () {
    hide(androidBlock);
    hide(iosBlock);
    hide(genericBlock);
    show(installDone);
  });
};
