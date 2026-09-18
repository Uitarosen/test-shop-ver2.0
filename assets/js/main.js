/* =========================================================
   AUGUST SHOP — interactions
   スクロール演出 / ドロワー / タブ / アコーディオン /
   クーポンコピー / 買取フォーム送信
   ========================================================= */
(() => {
  'use strict';

  /* ---------- リロード時のスクロール位置ズレを防ぐ ----------
     ブラウザの自動スクロール復元を無効化し、横位置は常に0へ戻す。 */
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  const resetX = () => {
    if (window.scrollX !== 0) window.scrollTo(0, window.scrollY);
  };
  window.addEventListener('load', resetX);
  window.addEventListener('resize', resetX, { passive: true });

  const header = document.getElementById('header');
  const burger = document.getElementById('burger');
  const drawer = document.getElementById('drawer');
  const topbar = document.querySelector('.topbar');

  const chromeHeight = () => (header ? header.offsetHeight : 0) + (topbar ? topbar.offsetHeight : 0);

  /* ---------- Header state on scroll ---------- */
  const onScroll = () => {
    const y = window.scrollY;
    if (header) header.classList.toggle('is-stuck', y > 40 || !document.querySelector('.hero'));
    document.body.classList.toggle('is-scrolled', y > 220);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile drawer ---------- */
  if (burger && drawer) {
    const FOCUSABLE = 'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

    const setNav = (open) => {
      document.body.classList.toggle('nav-open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
      drawer.setAttribute('aria-hidden', String(!open));
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) {
        const first = drawer.querySelector(FOCUSABLE);
        if (first) first.focus();
      } else {
        burger.focus();
      }
    };

    burger.addEventListener('click', () => setNav(!document.body.classList.contains('nav-open')));
    drawer.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => setNav(false)));

    document.addEventListener('keydown', (e) => {
      if (!document.body.classList.contains('nav-open')) return;

      if (e.key === 'Escape') {
        setNav(false);
        return;
      }

      /* ドロワーを開いている間はフォーカスを内側に閉じ込める */
      if (e.key !== 'Tab') return;
      const items = [burger, ...drawer.querySelectorAll(FOCUSABLE)];
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });
  }

  /* ---------- Scroll reveal ---------- */
  const revealables = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.06 }
    );
    revealables.forEach((el) => io.observe(el));
  } else {
    revealables.forEach((el) => el.classList.add('is-in'));
  }

  /* ---------- Stats count up ---------- */
  const counters = document.querySelectorAll('[data-count]');
  const animateCount = (el) => {
    const target = Number(el.dataset.count);
    if (!target) {
      el.textContent = String(target);
      return;
    }
    const duration = 1300;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      el.textContent = String(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  if ('IntersectionObserver' in window && counters.length) {
    const countIo = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          animateCount(entry.target);
          countIo.unobserve(entry.target);
        });
      },
      { threshold: 0.6 }
    );
    counters.forEach((el) => countIo.observe(el));
  } else {
    counters.forEach((el) => { el.textContent = el.dataset.count; });
  }

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll('.acc__q').forEach((btn) => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.acc__item');
      const open = item.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  /* ---------- Coupon copy ---------- */
  document.querySelectorAll('[data-coupon]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const code = btn.dataset.coupon;
      try {
        await navigator.clipboard.writeText(code);
      } catch (err) {
        /* clipboard 非対応環境は無視 */
      }
      const label = btn.querySelector('.coupon__copy');
      if (!label) return;
      const original = label.textContent;
      label.textContent = 'コピーしました';
      btn.classList.add('is-copied');
      setTimeout(() => {
        label.textContent = original;
        btn.classList.remove('is-copied');
      }, 1800);
    });
  });

  /* ---------- Buy-method tabs ---------- */
  document.querySelectorAll('[data-tabs]').forEach((root) => {
    const tabs = root.querySelectorAll('[data-tab]');
    const panels = root.querySelectorAll('[data-panel]');
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        tabs.forEach((t) => {
          t.classList.toggle('is-active', t === tab);
          t.setAttribute('aria-selected', String(t === tab));
        });
        panels.forEach((p) => p.classList.toggle('is-active', p.dataset.panel === tab.dataset.tab));
      });
    });
  });

  /* ---------- Buy form ----------
     form[data-endpoint] に送信先URLが設定されていれば fetch で送信します。
     未設定の場合は「送信できた」と誤解させないよう、LINE・メールでの連絡をご案内します。 */
  const form = document.getElementById('buyform');
  if (form) {
    const done = document.getElementById('formdone');
    const submitBtn = form.querySelector('[type="submit"]');

    const showNote = (html, isError) => {
      let note = form.querySelector('.formnote');
      if (!note) {
        note = document.createElement('p');
        note.className = 'formnote';
        note.setAttribute('role', 'status');
        form.appendChild(note);
      }
      note.classList.toggle('formnote--error', Boolean(isError));
      note.innerHTML = html;
      note.scrollIntoView({ block: 'center', behavior: 'smooth' });
    };

    const showDone = () => {
      form.classList.add('is-sent');
      form.reset();
      if (!done) return;
      done.hidden = false;
      window.scrollTo({
        top: done.getBoundingClientRect().top + window.scrollY - chromeHeight() - 20,
        behavior: 'smooth'
      });
    };

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;

      const endpoint = (form.dataset.endpoint || '').trim();
      if (!endpoint) {
        showNote(
          'ただいまフォームからの送信を受け付けておりません。お手数ですが、' +
            '<a href="https://line.me/R/ti/p/%40776yyqfq" target="_blank" rel="noopener">LINE</a> または ' +
            '<a href="mailto:kaitori@august-shop.net">kaitori@august-shop.net</a> までご連絡ください。',
          true
        );
        return;
      }

      if (submitBtn) submitBtn.setAttribute('aria-busy', 'true');
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          body: new FormData(form),
          headers: { Accept: 'application/json' }
        });
        if (!res.ok) throw new Error('request failed: ' + res.status);
        showDone();
      } catch (err) {
        showNote(
          '送信に失敗しました。通信環境をご確認のうえ、再度お試しください。解決しない場合は ' +
            '<a href="mailto:kaitori@august-shop.net">kaitori@august-shop.net</a> までご連絡ください。',
          true
        );
      } finally {
        if (submitBtn) submitBtn.removeAttribute('aria-busy');
      }
    });
  }

  /* ---------- Skip link ---------- */
  const skip = document.querySelector('.skiplink');
  const mainEl = document.getElementById('top');
  if (skip && mainEl) {
    skip.addEventListener('click', () => {
      mainEl.setAttribute('tabindex', '-1');
      mainEl.focus({ preventScroll: true });
    });
  }

  /* ---------- Anchor offset for fixed chrome ---------- */
  document.querySelectorAll('a[href*="#"]').forEach((a) => {
    const url = new URL(a.getAttribute('href'), location.href);
    const samePage = url.pathname === location.pathname && url.hash;
    if (!samePage) return;
    a.addEventListener('click', (e) => {
      const target = document.querySelector(url.hash);
      if (!target) return;
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - chromeHeight() + 1;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

  /* ---------- Deep link offset on load ---------- */
  if (location.hash) {
    const target = document.querySelector(location.hash);
    if (target) {
      setTimeout(() => {
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - chromeHeight() + 1 });
      }, 60);
    }
  }
})();
