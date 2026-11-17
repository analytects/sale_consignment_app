(function () {
  "use strict";
  var root = document.documentElement;
  var KEY = "cfo-guide-theme";

  function odooScheme() {
    var m = document.cookie.match(/(?:^|;\s*)color_scheme=(dark|light)/);
    return m ? m[1] : null;
  }
  function currentTheme() {
    var stored = null;
    try { stored = localStorage.getItem(KEY); } catch (e) { /* storage blocked */ }
    return stored || odooScheme() || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  function applyTheme(t) {
    root.setAttribute("data-theme", t);
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.setAttribute("aria-pressed", t === "dark" ? "true" : "false");
      btn.setAttribute("aria-label", t === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    }
  }
  applyTheme(currentTheme());

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(currentTheme());
    var body = document.body;

    var themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        try { localStorage.setItem(KEY, next); } catch (e) { /* storage blocked */ }
        applyTheme(next);
      });
    }
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
      applyTheme(currentTheme());
    });

    // Contents sheet on narrow screens
    var tocBtn = document.getElementById("toc-toggle");
    function closeToc() {
      body.classList.remove("toc-open");
      if (tocBtn) tocBtn.setAttribute("aria-expanded", "false");
    }
    if (tocBtn) {
      tocBtn.addEventListener("click", function () {
        var open = body.classList.toggle("toc-open");
        tocBtn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
    document.querySelectorAll(".side a[href^='#']").forEach(function (a) {
      a.addEventListener("click", closeToc);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { closeToc(); closeLightbox(); }
    });

    // Active entry in the contents list
    var links = {};
    document.querySelectorAll(".side a[href^='#t-']").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    var tasks = Array.prototype.slice.call(document.querySelectorAll(".task"));
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            Object.keys(links).forEach(function (k) { links[k].classList.remove("is-active"); });
            var a = links[en.target.id];
            if (a) a.classList.add("is-active");
          }
        });
      }, { rootMargin: "-20% 0px -70% 0px" });
      tasks.forEach(function (t) { io.observe(t); });
    }

    // Task search
    var inputs = document.querySelectorAll("input[data-search]");
    var empty = document.querySelector(".no-results");
    var index = tasks.map(function (t) {
      return { el: t, text: t.textContent.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") };
    });
    function filter(q) {
      q = q.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      var shown = 0;
      index.forEach(function (it) {
        var hit = !q || it.text.indexOf(q) !== -1;
        it.el.hidden = !hit;
        var a = links[it.el.id];
        if (a) a.parentElement.hidden = !hit;
        if (hit) shown++;
      });
      if (empty) empty.classList.toggle("show", shown === 0);
      inputs.forEach(function (i) { if (i.value !== q && document.activeElement !== i) i.value = q; });
    }
    inputs.forEach(function (input) {
      input.addEventListener("input", function () { filter(input.value); });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          var first = tasks.filter(function (t) { return !t.hidden; })[0];
          if (first) { closeToc(); first.scrollIntoView({ behavior: "smooth", block: "start" }); }
        }
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement.tagName !== "INPUT") {
        var visible = Array.prototype.filter.call(inputs, function (i) { return i.offsetParent !== null; })[0];
        if (visible) { e.preventDefault(); visible.focus(); }
      }
    });

    // Screenshot zoom
    var box = document.getElementById("lightbox");
    var boxImg = box ? box.querySelector("img") : null;
    var lastFocus = null;
    function closeLightbox() {
      if (!box || !box.classList.contains("open")) return;
      box.classList.remove("open");
      box.setAttribute("aria-hidden", "true");
      if (lastFocus) lastFocus.focus();
    }
    document.querySelectorAll(".shot button").forEach(function (b) {
      b.addEventListener("click", function () {
        var img = b.querySelector("img");
        lastFocus = b;
        boxImg.src = img.currentSrc || img.src;
        boxImg.alt = img.alt;
        box.classList.add("open");
        box.setAttribute("aria-hidden", "false");
        box.querySelector("button").focus();
      });
    });
    if (box) box.addEventListener("click", closeLightbox);
  });
})();
