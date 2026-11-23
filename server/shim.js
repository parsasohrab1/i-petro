/* window.claude replacement for self-hosted iPetro: db (REST + server-sent events), user, assets, downloads, sample.
   "sample" exists only when the server has ANTHROPIC_API_KEY; otherwise use("sample") rejects and the dashboard switches
   off Claude scoring by itself. */
(function () {
  "use strict";
  var H = { "X-Requested-With": "ppt" };

  function api(method, url, body, raw) {
    var opt = { method: method, headers: Object.assign({}, H), credentials: "same-origin" };
    if (body !== undefined && !raw) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    if (raw) opt.body = raw;
    return fetch(url, opt).then(function (r) {
      if (r.status === 401) { location.href = "/login"; return new Promise(function () {}); }
      if (!r.ok) { var e = new Error("HTTP " + r.status); e.code = r.status === 403 ? "invalid_argument" : "http_" + r.status; throw e; }
      return r.json();
    });
  }

  // ---- live updates: every open snapshot refetches when the server says its document or collection changed
  var watchers = new Set(), timer = null, es = null;
  function connect() {
    if (es) return;
    es = new EventSource("/api/events");
    es.onmessage = function (m) {
      var ev; try { ev = JSON.parse(m.data); } catch (e) { return; }
      watchers.forEach(function (w) { if (w.path === ev.path || w.path === ev.parent) w.schedule(); });
    };
    es.onopen = function () { watchers.forEach(function (w) { w.schedule(); }); };   // resync after a reconnect
  }

  function docSnap(id, r) { return { id: id, exists: !!r.exists, data: function () { return r.exists ? r.data : undefined; } }; }
  function colSnap(r) {
    var docs = r.docs.map(function (d) { return { id: d.id, exists: true, data: function () { return d.data; } }; });
    return { docs: docs, size: docs.length, empty: docs.length === 0, forEach: function (f) { docs.forEach(f); } };
  }
  function watch(path, fetcher, cb, err) {
    var w = { path: path, schedule: function () { clearTimeout(w.t); w.t = setTimeout(run, 120); } };
    function run() { fetcher().then(cb, function (e) { if (err) err(e); }); }
    watchers.add(w); connect(); run();
    return function () { watchers.delete(w); clearTimeout(w.t); };
  }
  var q = encodeURIComponent;

  var dbApi = {
    doc: function (path) {
      path = path.replace(/^\/+|\/+$/g, "");
      var id = path.split("/").pop();
      var get = function () { return api("GET", "/api/doc?path=" + q(path)).then(function (r) { return docSnap(id, r); }); };
      return {
        id: id, path: path, get: get,
        set: function (data) { return api("PUT", "/api/doc?path=" + q(path), data); },
        update: function (data) {   // merge fields into the stored document (the page uses it for score and status edits)
          return get().then(function (s) { if (!s.exists) throw new Error("not-found"); return api("PUT", "/api/doc?path=" + q(path), Object.assign({}, s.data(), data)); });
        },
        delete: function () { return api("DELETE", "/api/doc?path=" + q(path)); },
        onSnapshot: function (cb, err) { return watch(path, get, cb, err); }
      };
    },
    collection: function (path) {
      path = path.replace(/^\/+|\/+$/g, "");
      var get = function () { return api("GET", "/api/col?path=" + q(path)).then(colSnap); };
      var col = { path: path, get: get, onSnapshot: function (cb, err) { return watch(path, get, cb, err); } };
      col.where = function (field, op, val) {   // only "==" is used by the page; filtering happens in the browser
        if (op !== "==") throw new Error("where: only == is supported");
        var sub = { get: function () { return get().then(function (snap) { return colSnap({ docs: snap.docs.filter(function (d) { return d.data()[field] === val; }).map(function (d) { return { id: d.id, data: d.data() }; }) }); }); } };
        sub.onSnapshot = function (cb, err) { return watch(path, sub.get, cb, err); };
        return sub;
      };
      return col;
    }
  };

  var services = {
    db: function () { return dbApi; },
    user: function () {
      return api("GET", "/api/me").then(function (me) {
        return { me: function () { return Promise.resolve(me); }, can: function () { return Promise.resolve(true); } };
      });
    },
    assets: function () {
      return {
        upload: function (file) {
          var fd = new FormData(); fd.append("file", file, file.name || "file");
          return api("POST", "/api/assets", undefined, fd);
        }
      };
    },
    sample: function () {
      return api("GET", "/api/sample/status").then(function (st) {
        if (!st.enabled) throw new Error("service not available: sample");
        function parseJson(t) {
          t = String(t).trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
          try { return JSON.parse(t); } catch (e) {
            var a = t.search(/[\[{]/), b = Math.max(t.lastIndexOf("}"), t.lastIndexOf("]"));
            if (a >= 0 && b > a) return JSON.parse(t.slice(a, b + 1));
            throw e;
          }
        }
        var call = function (input, opts) { return api("POST", "/api/sample", { input: input, tier: (opts && opts.modelTier) || "default" }); };
        var fn = function (input, opts) { return call(input, opts); };
        fn.json = function (input, opts) {
          var inp = typeof input === "string" ? input + "\n\nReply with valid JSON only, no other text." : input;
          return call(inp, opts).then(function (r) { return parseJson(r.text); });
        };
        return fn;
      });
    },
    downloads: function () {
      return {
        save: function (o) {
          var blob = o.data instanceof Blob ? o.data : new Blob([o.data]);
          var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = o.filename || "file";
          document.body.appendChild(a); a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
          return Promise.resolve();
        }
      };
    }
  };

  window.claude = {
    use: function (name) {
      if (!services[name]) return Promise.reject(new Error("service not available: " + name));
      try { return Promise.resolve(services[name]()); } catch (e) { return Promise.reject(e); }
    }
  };
})();
