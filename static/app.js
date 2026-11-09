(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  async function ask(q) {
    const answer = $("answer");
    try {
      const res = await fetch(`/api/ask?q=${encodeURIComponent(q)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      $("trace").innerHTML =
        `<span>GET /api/ask</span><span>query → <b>${data.terms.length}</b> terms</span>` +
        `<span>top-k <b>${data.hits.length}</b>/${data.indexed}</span><span><b>${data.ms}</b> ms</span>`;
      $("hits").innerHTML = data.hits
        .map((h, n) => `<li class="hit"><span class="n">[${n + 1}]</span><span>${esc(h.title)}<span class="src">${esc(h.id)}</span></span><span class="sc">${h.score.toFixed(2)}</span></li>`)
        .join("");
      answer.innerHTML = data.hits.length
        ? `<span class="lbl">Grounded answer</span>` + data.hits.map((h, n) => `<p>${esc(h.answer)}<sup>[${n + 1}]</sup></p>`).join("")
        : `<span class="lbl">No match</span><p>Nothing in the index matches that. Try agents, RAG, Kafka, scale, AWS or mentoring.</p>`;
    } catch (err) {
      $("hits").innerHTML = "";
      answer.innerHTML = `<span class="lbl">Retriever unavailable</span><p>The API didn't respond (${esc(err.message)}). Refresh the page to try again.</p>`;
    }
  }

  $("qform").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = $("qin").value.trim();
    if (q) ask(q);
  });
  document.querySelectorAll("[data-q]").forEach((b) =>
    b.addEventListener("click", () => { $("qin").value = b.dataset.q; ask(b.dataset.q); })
  );

  $("copy").addEventListener("click", (e) => {
    const b = e.currentTarget;
    const mail = $("mail");
    const select = () => {
      const r = document.createRange(); r.selectNodeContents(mail);
      const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      b.textContent = "Selected";
    };
    try {
      navigator.clipboard.writeText(mail.textContent).then(() => {
        b.textContent = "Copied"; setTimeout(() => (b.textContent = "Copy"), 1600);
      }, select);
    } catch { select(); }
  });

  ask($("qin").value);
})();
