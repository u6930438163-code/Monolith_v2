(() => {
  const agents = ["Aria", "Alex", "Astyria", "Aurelius"];
  const app = document.querySelector("#app");
  const login = document.querySelector("#login");
  const toast = document.querySelector("#toast");
  const messages = document.querySelector("#chat-messages");
  let selectedAgent = "local";
  let currentView = "chat";
  let socket;
  let toastTimer;
  let socketRetry;
  const state = { snapshot: null, logs: [], terminal: [], files: null };
  const labels = { chat: "Czat AI", terminal: "Terminal", files: "Eksplorator plików", processes: "Procesy", logs: "Logi", ollama: "Ollama", hyperspace: "Hiperprzestrzeń" };

  async function api(path, options = {}) {
    const response = await fetch(path, { credentials: "same-origin", ...options, headers: { "Content-Type": "application/json", ...options.headers } });
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) {
      showLogin();
      throw new Error("Sesja wygasła. Zaloguj się ponownie.");
    }
    if (!response.ok) {
      const failures = data.results?.map(item => `${item.agent}: ${statusLabel(item.status)}`).join(", ");
      throw new Error(failures ? `${data.error} · ${failures}` : data.error || `Błąd serwera (${response.status})`);
    }
    return data;
  }

  function showLogin() {
    if (socket) socket.close();
    app.hidden = true;
    login.hidden = false;
  }

  function showApp() {
    login.hidden = true;
    app.hidden = false;
    connectSocket();
    refresh();
  }

  function notify(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
  }

  function addActivity(message) {
    const feed = document.querySelector("#activity-feed");
    feed.querySelector(".empty-note")?.remove();
    const item = document.createElement("div");
    item.className = "activity-item";
    const time = document.createElement("time");
    time.textContent = new Date().toLocaleTimeString("pl-PL");
    item.append(time, document.createTextNode(message));
    feed.prepend(item);
    while (feed.children.length > 8) feed.lastElementChild.remove();
  }

  function statusLabel(status) {
    return ({ connected: "Połączono", configured: "Skonfigurowany", not_verified: "Niezweryfikowany", not_connected: "Brak połączenia", no_data: "Brak danych", unavailable: "Niedostępny" })[status] || status || "Nieznany";
  }

  function updateStatus(snapshot) {
    state.snapshot = snapshot;
    const list = document.querySelector("#system-status");
    const checks = [
      ["◈", "Czat lokalny", snapshot.ollama?.status === "connected" ? "Ollama dostępna" : statusLabel(snapshot.ollama?.status), snapshot.ollama?.status === "connected" ? "ok" : "warn"],
      ["◫", "Diagnostyka", snapshot.diagnostics?.status === "available" ? "Dane systemowe dostępne" : "Brak danych", snapshot.diagnostics?.status === "available" ? "ok" : ""],
      ["⬡", "Ollama", snapshot.ollama?.status === "connected" ? `${snapshot.ollama?.data?.length || 0} modeli` : statusLabel(snapshot.ollama?.status), snapshot.ollama?.status === "connected" ? "ok" : "warn"],
    ];
    list.replaceChildren(...checks.map(([icon, name, detail, stateClass]) => {
      const row = document.createElement("div");
      row.className = "system-row";
      const symbol = document.createElement("span");
      symbol.className = "system-icon";
      symbol.textContent = icon;
      const copy = document.createElement("span");
      copy.className = "system-copy";
      const title = document.createElement("strong");
      title.textContent = name;
      const small = document.createElement("small");
      small.textContent = detail;
      copy.append(title, small);
      const indicator = document.createElement("i");
      indicator.className = `system-indicator ${stateClass}`;
      row.append(symbol, copy, indicator);
      return row;
    }));
    const listAgents = document.querySelector("#agent-status");
    listAgents.replaceChildren(...agents.map(name => {
      const agent = snapshot.agent_status?.[name] || { status: "not_connected" };
      const row = document.createElement("div");
      row.className = "mini-agent";
      const avatar = document.createElement("span");
      avatar.className = `agent-avatar ${name.toLowerCase()}`;
      avatar.textContent = name[0];
      const label = document.createElement("span");
      label.className = "mini-agent-name";
      label.textContent = name;
      const status = document.createElement("span");
      status.className = `mini-agent-state ${agent.status === "connected" ? "connected" : ""}`;
      status.textContent = statusLabel(agent.status);
      row.append(avatar, label, status);
      return row;
    }));
    document.querySelectorAll(".agent-item[data-agent]").forEach(button => {
      const status = snapshot.agent_status?.[button.dataset.agent]?.status;
      button.querySelector(".status-dot")?.classList.toggle("connected", status === "connected");
    });
    document.querySelector("#statusbar-message").textContent = `Dane rzeczywiste · ${new Date(snapshot.timestamp_utc).toLocaleTimeString("pl-PL")}`;
    if (currentView === "processes") renderProcesses();
    if (currentView === "ollama") renderOllama();
  }

  async function refresh() {
    try {
      const result = await api("/api/v1/status");
      updateStatus(result);
    } catch (error) {
      notify(error.message);
    }
  }

  function connectSocket() {
    clearTimeout(socketRetry);
    if (socket) socket.close();
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocol}//${location.host}/ws`);
    socket.onopen = () => {
      document.querySelector("#connection-label").textContent = "Połączono";
      document.querySelector("#connection-dot").classList.add("pulse");
      const live = document.querySelector("#live-status");
      live.classList.add("connected");
      live.lastChild.textContent = " Live";
    };
    socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "status") updateStatus(data.payload);
        if (data.type === "event") addActivity(data.message);
      } catch {
        addActivity("Otrzymano nieprawidłowe zdarzenie czasu rzeczywistego.");
      }
    };
    socket.onclose = () => {
      document.querySelector("#connection-label").textContent = "Brak synchronizacji";
      const live = document.querySelector("#live-status");
      live.classList.remove("connected");
      live.lastChild.textContent = " Polling";
      socketRetry = setTimeout(connectSocket, 5000);
    };
    socket.onerror = () => socket.close();
  }

  function addMessage(role, text, author = role === "user" ? "Ty" : "Monolith AI", error = false) {
    const box = document.createElement("article");
    box.className = `message ${role === "user" ? "user" : ""} ${error ? "message-error" : ""}`;
    const meta = document.createElement("span");
    meta.className = "message-meta";
    meta.textContent = author;
    const content = document.createElement("span");
    content.textContent = text;
    box.append(meta, content);
    messages.append(box);
    box.scrollIntoView({ block: "nearest", behavior: "smooth" });
    return box;
  }

  async function sendMessage(text) {
    const target = selectedAgent;
    const author = target === "local" ? "Monolith AI" : target === "all" ? "Wszyscy agenci" : target;
    addMessage("user", text);
    const pending = addMessage("assistant", "Łączenie z rzeczywistym źródłem…", author);
    try {
      const result = await api("/api/v1/chat", { method: "POST", body: JSON.stringify({ message: text, agent: target }) });
      pending.lastElementChild.textContent = result.reply;
      pending.querySelector(".message-meta").textContent = `${author} · ${result.source}${result.model ? ` · ${result.model}` : ""}`;
      addActivity(`${author}: wiadomość dostarczona (${result.source}).`);
    } catch (error) {
      pending.classList.add("message-error");
      pending.lastElementChild.textContent = `${error.message} Brak odpowiedzi — niczego nie symulowano.`;
      addActivity(`${author}: żądanie nie powiodło się.`);
    }
  }

  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  function toolShell(title, description) {
    const content = document.querySelector("#tool-content");
    content.innerHTML = `<span class="eyebrow">NARZĘDZIA WORKSPACE</span><h1 class="tool-title">${esc(title)}</h1><p class="tool-description">${esc(description)}</p>`;
    return content;
  }

  async function renderProcesses() {
    const content = toolShell("Procesy i diagnostyka", "Odczyt systemu z lokalnego środowiska backendu. Tylko rzeczywiste dane.");
    const diagnostic = state.snapshot?.diagnostics?.data;
    if (!diagnostic) {
      content.insertAdjacentHTML("beforeend", '<div class="tool-card"><p class="empty-note">Diagnostyka nie zwróciła danych.</p></div>');
      return;
    }
    const format = bytes => bytes == null ? "—" : `${(bytes / 1024 / 1024).toFixed(0)} MB`;
    const metrics = [["CPU", diagnostic.cpu_percent == null ? "Brak danych" : `${diagnostic.cpu_percent}%`], ["Pamięć", diagnostic.memory ? `${diagnostic.memory.percent}% · ${format(diagnostic.memory.available)} dostępne` : "Brak danych"], ["Dysk /", diagnostic.disk ? `${diagnostic.disk.percent}% · ${format(diagnostic.disk.free)} wolne` : "Brak danych"], ["Load average", diagnostic.load_average?.join(" · ") || "Brak danych"], ["Uptime", diagnostic.uptime_seconds == null ? "Brak danych" : `${Math.floor(diagnostic.uptime_seconds / 3600)} h`]];
    content.insertAdjacentHTML("beforeend", `<div class="tool-card"><h2>Metryki lokalne</h2><table class="table"><tbody>${metrics.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")}</tbody></table></div><div class="tool-card"><h2>Procesy wg użycia pamięci</h2>${diagnostic.processes?.top_by_rss?.length ? `<table class="table"><thead><tr><th>PID</th><th>Proces</th><th>Pamięć</th></tr></thead><tbody>${diagnostic.processes.top_by_rss.map(proc => `<tr><td>${esc(proc.pid)}</td><td>${esc(proc.name)}</td><td>${format(proc.rss_bytes)}</td></tr>`).join("")}</tbody></table>` : '<p class="empty-note">Lista procesów niedostępna.</p>'}</div><div class="tool-card"><h2>Usługi</h2><table class="table"><tbody>${Object.entries(diagnostic.services || {}).map(([name, item]) => `<tr><td>${esc(name)}</td><td>${esc(item.state || statusLabel(item.status))}</td></tr>`).join("")}</tbody></table></div>`);
  }

  async function renderOllama() {
    const content = toolShell("Ollama", "Lokalny menedżer modeli. Generowanie odpowiedzi używa skonfigurowanego backendu.");
    const models = state.snapshot?.ollama?.data;
    content.insertAdjacentHTML("beforeend", `<div class="tool-card"><h2>Połączenie</h2><p class="empty-note">Ollama: ${esc(statusLabel(state.snapshot?.ollama?.status))} · źródło: ${esc(state.snapshot?.ollama?.source || "brak")}</p></div><div class="tool-card"><h2>Zainstalowane modele</h2>${Array.isArray(models) && models.length ? `<table class="table"><thead><tr><th>MODEL</th><th>ROZMIAR</th></tr></thead><tbody>${models.map(model => `<tr><td>${esc(model.name)}</td><td>${model.size ? `${(model.size / 1024 ** 3).toFixed(1)} GB` : "—"}</td></tr>`).join("")}</tbody></table>` : '<p class="empty-note">Brak dostępnych modeli lub brak połączenia z Ollama. Nie pokazujemy danych przykładowych.</p>'}</div><div class="tool-card"><h2>Pobierz model</h2><p class="empty-note">Pobieranie wybranego modelu do skonfigurowanego serwera Ollama może wymagać znacznego transferu i miejsca na dysku.</p><form id="pull-form" class="tool-form"><input class="tool-input" name="model" placeholder="np. llama3.2:3b" maxlength="128" required><button class="small-button" type="submit">Pobierz model</button></form></div>`);
    content.querySelector("#pull-form").addEventListener("submit", async event => {
      event.preventDefault();
      const button = event.currentTarget.querySelector("button");
      button.disabled = true;
      button.textContent = "Pobieranie…";
      try {
        const result = await api("/api/v1/ollama/pull", { method: "POST", body: JSON.stringify({ model: new FormData(event.currentTarget).get("model") }) });
        notify(`Pobieranie ${result.model} zakończone.`);
        await refresh();
      } catch (error) {
        notify(error.message);
      } finally {
        button.disabled = false;
        button.textContent = "Pobierz model";
      }
    });
  }

  async function renderFiles(path = "") {
    const content = toolShell("Eksplorator plików", "Tylko do odczytu · dostęp ograniczony do katalogu projektu.");
    try {
      const result = await api(`/api/v1/files?path=${encodeURIComponent(path)}`);
      state.files = result;
      const crumb = result.path ? `<button class="text-button" data-path="">Projekt</button><span>/ ${esc(result.path)}</span>` : "<span>Projekt główny</span>";
      content.insertAdjacentHTML("beforeend", `<div class="tool-card"><div class="panel-heading">${crumb}</div><table class="table"><thead><tr><th>NAZWA</th><th>TYP</th><th>ROZMIAR</th></tr></thead><tbody>${result.entries.map(entry => `<tr><td>${entry.type === "directory" ? `<button class="text-button" data-path="${esc([result.path, entry.name].filter(Boolean).join("/"))}">▤ ${esc(entry.name)}</button>` : `<button class="text-button" data-file="${esc([result.path, entry.name].filter(Boolean).join("/"))}">${esc(entry.name)}</button>`}</td><td>${entry.type === "directory" ? "Katalog" : "Plik"}</td><td>${entry.size == null ? "—" : esc(entry.size)}</td></tr>`).join("") || '<tr><td colspan="3">Pusty katalog.</td></tr>'}</tbody></table></div><div id="file-preview"></div>`);
      content.querySelectorAll("[data-path]").forEach(button => button.addEventListener("click", () => renderFiles(button.dataset.path)));
      content.querySelectorAll("[data-file]").forEach(button => button.addEventListener("click", async () => {
        try {
          const file = await api(`/api/v1/files?path=${encodeURIComponent(button.dataset.file)}`);
          content.querySelector("#file-preview").innerHTML = `<div class="tool-card"><h2>${esc(file.path)}</h2><pre class="tool-output">${esc(file.content)}</pre></div>`;
        } catch (error) { notify(error.message); }
      }));
    } catch (error) { content.insertAdjacentHTML("beforeend", `<div class="tool-card"><p class="error-text">${esc(error.message)}</p></div>`); }
  }

  async function renderLogs() {
    const content = toolShell("Logi", "Rzeczywiste zdarzenia backendu. Treść czatu, sekrety i tokeny nie są logowane.");
    const result = await api("/api/v1/logs");
    content.insertAdjacentHTML("beforeend", `<div class="tool-card"><h2>Zdarzenia usługi</h2><pre class="tool-output">${esc(result.entries.length ? result.entries.map(entry => `${entry.timestamp}  ${entry.level.padEnd(5)}  ${entry.event}`).join("\n") : "Brak zarejestrowanych zdarzeń.")}</pre></div>`);
  }

  async function renderTerminal() {
    const content = toolShell("Terminal", "Ograniczony terminal do odczytu i diagnostyki. Nie wykonuje powłoki ani dowolnych poleceń.");
    content.insertAdjacentHTML("beforeend", '<div class="tool-card"><h2>Sesja lokalna</h2><pre id="terminal-output" class="tool-output"></pre><form id="terminal-form" class="tool-form"><span class="context-icon">›_</span><input class="tool-input" name="command" autocomplete="off" placeholder="help" aria-label="Polecenie terminala"><button class="small-button" type="submit">Uruchom</button></form><p class="empty-note">Dozwolone: help, pwd, ls, cat, git status, git log, python --version, ps.</p></div>');
    const output = content.querySelector("#terminal-output");
    output.textContent = state.terminal.map(item => `$ ${item.command}\n${item.output}`).join("\n");
    content.querySelector("#terminal-form").addEventListener("submit", async event => {
      event.preventDefault();
      const command = new FormData(event.currentTarget).get("command");
      try {
        const result = await api("/api/v1/terminal", { method: "POST", body: JSON.stringify({ command }) });
        state.terminal.push({ command, output: result.output });
        if (state.terminal.length > 40) state.terminal.shift();
        await renderTerminal();
        document.querySelector(".tool-input").focus();
      } catch (error) { notify(error.message); }
    });
  }

  async function renderHyperspace() {
    const content = toolShell("Komunikacja hiperprzestrzenią", "Wyłącznie uwierzytelnione transmisje z zewnętrznego, skonfigurowanego źródła HTTPS. Bez przechwytywania sygnałów i symulacji.");
    try {
      const result = await api("/api/v1/hyperspace");
      const records = result.transmissions;
      content.insertAdjacentHTML("beforeend", `<div class="tool-card"><h2>Status połączenia</h2><p class="empty-note">Źródło: ${esc(result.source || "brak skonfigurowanego endpointu")}<br>Status: ${esc(statusLabel(result.status))}<br>Ostatnie sprawdzenie: ${esc(result.timestamp_utc)}</p></div><div class="tool-card"><h2>Uwierzytelnione transmisje</h2>${records?.length ? `<table class="table"><thead><tr><th>ŹRÓDŁO</th><th>DATA UTC</th><th>WIADOMOŚĆ</th></tr></thead><tbody>${records.map(item => `<tr><td>${esc(item.source)}</td><td>${esc(item.timestamp_utc)}</td><td>${esc(item.message)}</td></tr>`).join("")}</tbody></table>` : '<p class="empty-note">Brak zweryfikowanych transmisji. Skonfiguruj własne HTTPS API i token w środowisku serwera.</p>'}</div>`);
    } catch (error) { content.insertAdjacentHTML("beforeend", `<div class="tool-card"><p class="error-text">${esc(error.message)}</p></div>`); }
  }

  async function setView(view) {
    currentView = view;
    document.querySelectorAll(".nav-item[data-view]").forEach(item => item.classList.toggle("active", item.dataset.view === view));
    document.querySelector("#view-title").textContent = labels[view] || "Czat AI";
    document.querySelector("#chat-view").hidden = view !== "chat";
    document.querySelector("#tool-view").hidden = view === "chat";
    if (view === "processes") renderProcesses();
    if (view === "files") renderFiles();
    if (view === "logs") {
      try { await renderLogs(); } catch (error) { notify(error.message); }
    }
    if (view === "terminal") renderTerminal();
    if (view === "ollama") renderOllama();
    if (view === "hyperspace") await renderHyperspace();
  }

  function selectAgent(agent) {
    selectedAgent = agent;
    currentView = "chat";
    setView("chat");
    const heading = document.querySelector("#chat-heading");
    const composer = document.querySelector("#composer-context");
    if (agent === "local") {
      heading.innerHTML = "Co dziś<br><span>zbudujemy?</span>";
      composer.innerHTML = '<span class="context-icon">◈</span><span>Monolith AI</span><span class="context-model">lokalny model</span>';
    } else {
      const name = agent === "all" ? "Wszyscy agenci" : agent;
      heading.innerHTML = `Kanał<br><span>${name === "Wszyscy agenci" ? "zespołu" : name}</span>`;
      composer.replaceChildren();
      const label = document.createElement("span");
      label.className = "context-icon";
      label.textContent = "◈";
      const channel = document.createElement("span");
      channel.textContent = name;
      composer.append(label, channel);
      if (agent !== "all" && state.snapshot?.agent_status?.[agent]?.status !== "connected") {
        const warning = document.createElement("span");
        warning.className = "context-model";
        warning.textContent = "oczekiwanie na konfigurację endpointu";
        composer.append(warning);
      }
    }
    messages.replaceChildren();
    if (agent !== "local") addMessage("assistant", "Kanał gotowy. Wiadomości są dostarczane wyłącznie do skonfigurowanych, rzeczywistych endpointów. Brak połączenia zostanie zgłoszony — odpowiedzi nie są symulowane.", "System");
  }

  document.querySelector("#login-form").addEventListener("submit", async event => {
    event.preventDefault();
    const error = document.querySelector("#login-error");
    error.textContent = "";
    try {
      await api("/api/v1/login", { method: "POST", body: JSON.stringify({ password: new FormData(event.currentTarget).get("password") }) });
      event.currentTarget.reset();
      showApp();
    } catch (reason) { error.textContent = reason.message; }
  });
  document.querySelector("#logout").addEventListener("click", async () => {
    try { await api("/api/v1/logout", { method: "POST", body: "{}" }); } catch { /* The session may already have expired. */ }
    if (window.MONOLITH_PASSWORDLESS) showApp(); else showLogin();
  });
  document.querySelectorAll(".nav-item[data-view], .text-button[data-view]").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
  document.querySelectorAll(".agent-item[data-agent]").forEach(button => button.addEventListener("click", () => selectAgent(button.dataset.agent)));
  document.querySelector("#refresh").addEventListener("click", () => refresh());
  document.querySelector("#chat-form").addEventListener("submit", async event => {
    event.preventDefault();
    const input = document.querySelector("#chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.style.height = "auto";
    await sendMessage(message);
  });
  document.querySelector("#chat-input").addEventListener("input", event => {
    event.target.style.height = "auto";
    event.target.style.height = `${Math.min(event.target.scrollHeight, 160)}px`;
  });
  document.querySelector("#chat-input").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      document.querySelector("#chat-form").requestSubmit();
    }
  });
  document.querySelector("#clock").textContent = new Intl.DateTimeFormat("pl-PL", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date()) + " UTC";
  api("/api/v1/session").then(() => showApp()).catch(() => {
    login.hidden = false;
    app.hidden = true;
    document.querySelector("#password").focus();
  });
})();
