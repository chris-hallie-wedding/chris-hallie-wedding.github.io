/* Language switching, mobile nav, and scroll reveal.
   Language resolution order:  ?lang= URL param  ->  saved choice  ->  browser  ->  vi
   The ?lang= param lets you send a targeted link, e.g. ...?lang=en to a friend abroad. */
(function () {
  "use strict";

  var DICT = window.I18N || {};
  var LANGS = Object.keys(DICT);
  var KEY = "kh-lang";

  function pick() {
    var q = new URLSearchParams(location.search).get("lang");
    if (q && DICT[q]) return q;
    try {
      var saved = localStorage.getItem(KEY);
      if (saved && DICT[saved]) return saved;
    } catch (e) { /* private mode: fall through */ }
    var navs = navigator.languages || [navigator.language || "vi"];
    for (var i = 0; i < navs.length; i++) {
      var base = String(navs[i]).toLowerCase().split("-")[0];
      if (DICT[base]) return base;
    }
    return "vi";
  }

  function apply(lang) {
    var d = DICT[lang];
    if (!d) return;

    document.documentElement.lang = lang;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var v = d[el.getAttribute("data-i18n")];
      if (v != null) el.textContent = v;
    });

    // data-i18n-attr="alt:gal.alt1" — translate an attribute rather than text
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
        var bits = pair.split(":");
        var v = d[bits[1] && bits[1].trim()];
        if (v != null) el.setAttribute(bits[0].trim(), v);
      });
    });

    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });

    try { localStorage.setItem(KEY, lang); } catch (e) { /* ignore */ }
  }

  apply(pick());

  document.querySelectorAll(".lang button").forEach(function (b) {
    b.addEventListener("click", function () { apply(b.dataset.lang); });
  });

  /* ── mobile nav ── */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ── scroll reveal ──
     Sections are visible in CSS by default; we only arm the animation once we
     know the observer is available, so a script failure can never hide content. */
  var items = document.querySelectorAll(".reveal");
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (still || !("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("in"); });
  } else {
    document.documentElement.classList.add("js-reveal");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    items.forEach(function (el) { io.observe(el); });
  }
})();
