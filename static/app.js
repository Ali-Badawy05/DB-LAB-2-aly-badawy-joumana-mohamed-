// Browser-side checks: same rules and same messages as app.py.
// The server checks everything again, so these are only for quick feedback.
(function () {
  function val(form, name) {
    var el = form.elements[name];
    return el ? el.value : "";
  }

  var rules = {
    register: function (f) {
      var e = [];
      if (!val(f, "name").trim()) e.push("Name is required");
      if (!val(f, "email").trim()) e.push("Email is required");
      if (!val(f, "password")) e.push("Password is required");
      if (!val(f, "confirm_password")) e.push("Confirm password is required");
      if (val(f, "password") && val(f, "confirm_password") &&
          val(f, "password") !== val(f, "confirm_password")) e.push("Passwords do not match");
      return e;
    },
    login: function (f) {
      var e = [];
      if (!val(f, "email").trim()) e.push("Email is required");
      if (!val(f, "password")) e.push("Password is required");
      return e;
    },
    todo: function (f) {
      var t = val(f, "title").trim();
      if (!t) return ["Title is required"];
      if (t.length > 200) return ["Title is too long (200 characters at most)"];
      return [];
    }
  };

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      var errors = rules[form.dataset.form](form);
      var box = form.querySelector(".errors");
      box.innerHTML = "";
      if (errors.length) {
        ev.preventDefault();  // nothing is sent to the server
        errors.forEach(function (msg) {
          var li = document.createElement("li");
          li.textContent = msg;
          box.appendChild(li);
        });
      }
    });
  });

  // R7: ask "are you sure?" before deleting
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      if (!window.confirm(form.dataset.confirm)) ev.preventDefault();
    });
  });
})();

// BONUS: dark mode toggle (remembered in the browser)
(function () {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;
  function paint() {
    var dark = document.documentElement.getAttribute("data-theme") === "dark";
    btn.textContent = dark ? "☀️" : "🌙";
  }
  paint();
  btn.addEventListener("click", function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
    paint();
  });
})();
