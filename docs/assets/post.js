/* Reading progress, and a left rail that marks the section you are in.
   The rail is built from the h2s on the page, so nothing has to be listed twice. */
(function () {
  var main = document.querySelector('main') || document.querySelector('.page');
  if (!main) return;
  var heads = [].slice.call(main.querySelectorAll('h2[id]'));

  var bar = document.querySelector('.progress i');
  function prog() {
    if (!bar) return;
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = 'scaleX(' + (h > 0 ? Math.min(1, window.scrollY / h) : 0) + ')';
  }

  var links = [];
  if (heads.length > 2) {
    var nav = document.createElement('nav');
    nav.className = 'railnav';
    nav.setAttribute('aria-label', 'Sections of this post');
    var html = '<p class="rail-title">In this post</p><ol>';
    heads.forEach(function (h) {
      var label = h.getAttribute('data-short') || h.textContent;
      html += '<li><a href="#' + h.id + '">' + label + '</a></li>';
    });
    nav.innerHTML = html + '</ol><a class="rail-top" href="#top">&uarr; Top</a>';
    document.body.appendChild(nav);
    links = [].slice.call(nav.querySelectorAll('ol a'));
  }

  function spy() {
    var mark = window.scrollY + 140;
    var cur = -1;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top + window.scrollY <= mark) cur = i;
    }
    links.forEach(function (a, i) { a.classList.toggle('is-current', i === cur); });
    document.body.dataset.rail = window.scrollY > main.offsetTop - 120 ? 'on' : 'off';
  }

  var queued = false;
  function onScroll() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; prog(); spy(); });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  prog();
  spy();
})();
