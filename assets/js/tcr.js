/* The Conjoncture Review — interactions du site. Sans dépendance. */
(function () {
  "use strict";

  var BASE = (function () {
    var link = document.querySelector('link[rel="alternate"][type="application/rss+xml"]');
    var href = link ? link.getAttribute("href") : "/flux.xml";
    return href.replace(/\/flux\.xml$/, "");
  })();

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };

  /* --- thème clair / sombre ---------------------------------------------- */
  var themeBtn = $("[data-theme-toggle]");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var current = document.documentElement.getAttribute("data-theme") || (dark ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("tcr-theme", next); } catch (e) {}
    });
  }

  /* --- menu mobile -------------------------------------------------------- */
  var burger = $("[data-nav-toggle]");
  var rubnav = $("#nav-rubriques");
  if (burger && rubnav) {
    burger.addEventListener("click", function () {
      var open = rubnav.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
    });
  }

  /* --- retour en haut ----------------------------------------------------- */
  var toTop = $("[data-to-top]");
  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    var onScroll = function () {
      toTop.classList.toggle("is-visible", window.scrollY > 700);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* --- copie du lien ------------------------------------------------------ */
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var url = btn.getAttribute("data-copy");
      var done = function () {
        btn.setAttribute("data-copied", "");
        btn.setAttribute("title", "Lien copié");
        setTimeout(function () {
          btn.removeAttribute("data-copied");
          btn.setAttribute("title", "Copier le lien");
        }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, function () {});
      } else {
        var tmp = document.createElement("textarea");
        tmp.value = url;
        document.body.appendChild(tmp);
        tmp.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(tmp);
      }
    });
  });

  /* --- sommaire : mise en évidence de la section lue ---------------------- */
  var tocLinks = $$(".toc__item a");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a.parentNode; });
    var heads = $$(".prose h2[id], .prose h3[id]");
    var seen = new Set();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) seen.add(entry.target.id); else seen.delete(entry.target.id);
      });
      var active = heads.filter(function (h) { return seen.has(h.id); })[0];
      Object.keys(map).forEach(function (id) {
        map[id].classList.toggle("is-current", Boolean(active) && active.id === id);
      });
    }, { rootMargin: "-25% 0px -65% 0px" });
    heads.forEach(function (h) { observer.observe(h); });
  }

  /* --- filtres d'archives ------------------------------------------------- */
  var filters = $("[data-filters]");
  if (filters) {
    filters.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-filter]");
      if (!btn) return;
      var want = btn.getAttribute("data-filter");
      $$("[data-filter]", filters).forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      $$(".arch__row").forEach(function (row) {
        row.hidden = want !== "all" && row.getAttribute("data-rub") !== want;
      });
      $$(".arch").forEach(function (block) {
        block.hidden = $$(".arch__row:not([hidden])", block).length === 0;
      });
    });
  }

  /* --- newsletter --------------------------------------------------------- */
  var newsForm = $("[data-newsletter]");
  if (newsForm) {
    newsForm.addEventListener("submit", function (event) {
      var action = newsForm.getAttribute("action");
      if (action && action !== "#") return; // un service est configuré : on le laisse faire
      event.preventDefault();
      var legal = $(".news__legal", newsForm);
      if (legal) {
        legal.setAttribute("data-state", "pending");
        legal.textContent =
          "Formulaire non connecté : renseignez « newsletter_action » dans site.json.";
      }
    });
  }

  /* --- recherche ---------------------------------------------------------- */
  var indexPromise = null;
  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(BASE + "/recherche/index.json")
        .then(function (r) { return r.json(); })
        .catch(function () { return []; });
    }
    return indexPromise;
  }

  function fold(text) {
    return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function search(records, query) {
    var terms = fold(query).split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    return records
      .map(function (rec) {
        var score = 0;
        var title = fold(rec.t);
        for (var i = 0; i < terms.length; i++) {
          var term = terms[i];
          if (rec.k.indexOf(term) === -1) return null;
          score += title.indexOf(term) === 0 ? 6 : title.indexOf(term) > -1 ? 4 : 1;
        }
        return { rec: rec, score: score };
      })
      .filter(Boolean)
      .sort(function (a, b) { return b.score - a.score; })
      .map(function (hit) { return hit.rec; });
  }

  function resultHTML(rec) {
    var esc = function (s) {
      return String(s).replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
      });
    };
    return (
      '<a class="result" href="' + esc(rec.u) + '" style="--accent:' + esc(rec.a) + '">' +
      '<span class="result__rub">' + esc(rec.r) + "</span>" +
      '<span class="result__title">' + esc(rec.t) + "</span>" +
      '<span class="result__excerpt">' + esc(rec.e) + "</span>" +
      '<span class="result__foot">' + esc(rec.d) + " · " + esc(rec.m) + " min</span></a>"
    );
  }

  function wireSearch(input, target, emptyText) {
    var run = function () {
      var query = input.value.trim();
      if (query.length < 2) {
        target.innerHTML = query ? '<p class="noresult">Saisissez au moins deux caractères.</p>' : "";
        return;
      }
      loadIndex().then(function (records) {
        var hits = search(records, query);
        target.innerHTML = hits.length
          ? hits.slice(0, 20).map(resultHTML).join("")
          : '<p class="noresult">' + emptyText + " « " + query + " ».</p>";
      });
    };
    var timer;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(run, 120);
    });
    return run;
  }

  var box = $("[data-search]");
  if (box) {
    var boxInput = $("[data-search-input]", box);
    var boxResults = $("[data-search-results]", box);
    var runBox = wireSearch(boxInput, boxResults, "Aucun résultat pour");
    var open = function () {
      box.hidden = false;
      document.body.style.overflow = "hidden";
      boxInput.focus();
      loadIndex();
    };
    var close = function () {
      box.hidden = true;
      document.body.style.overflow = "";
    };
    $$("[data-search-open]").forEach(function (b) { b.addEventListener("click", open); });
    $$("[data-search-close]").forEach(function (b) { b.addEventListener("click", close); });
    box.addEventListener("click", function (e) { if (e.target === box) close(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !box.hidden) close();
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        box.hidden ? open() : close();
      }
      if (e.key === "/" && box.hidden && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
        e.preventDefault();
        open();
      }
    });
    void runBox;
  }

  var pageInput = $("[data-searchpage] input");
  if (pageInput) {
    var pageResults = $("[data-searchpage-results]");
    var runPage = wireSearch(pageInput, pageResults, "Aucun article ne correspond à");
    $("[data-searchpage]").addEventListener("submit", function (e) { e.preventDefault(); });
    var initial = new URLSearchParams(window.location.search).get("q");
    if (initial) {
      pageInput.value = initial;
      runPage();
    }
    pageInput.focus();
  }
})();
