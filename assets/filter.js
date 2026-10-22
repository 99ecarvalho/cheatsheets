// SPDX-License-Identifier: GPL-3.0-or-later
// Filter box for the cheat sheets: "/" focuses it, Esc clears it.
(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var sections = Array.prototype.slice.call(document.querySelectorAll('#grid section'));
  var none = document.getElementById('none');
  function apply() {
    var t = q.value.trim().toLowerCase();
    var any = false;
    sections.forEach(function (s) {
      var title = s.querySelector('h2').textContent.toLowerCase();
      var hit = 0;
      s.querySelectorAll('tr').forEach(function (r) {
        var show = !t || title.indexOf(t) > -1 || r.textContent.toLowerCase().indexOf(t) > -1;
        r.classList.toggle('hide', !show);
        if (show) hit++;
      });
      s.classList.toggle('empty', hit === 0);
      if (hit) any = true;
    });
    if (none) none.style.display = any ? 'none' : 'block';
  }
  q.addEventListener('input', apply);
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    else if (e.key === 'Escape' && document.activeElement === q) { q.value = ''; apply(); q.blur(); }
  });
})();
