import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./admin.css";

const API = "/admin/api";

const RESOURCE_GUIDE = {
  settings: "Telefon, manzil, logotip va saytning umumiy sozlamalari.",
  texts: "Sayt sahifalaridagi tahrirlanadigan qisqa matnlar.",
  slides: "Bosh sahifadagi katta suratlar va ularning yozuvlari.",
  directions: "Energiya auditi va qurilish nazorat o‘lchovi yo‘nalishlari.",
  services: "Har bir yo‘nalish ichidagi xizmatlar ro‘yxati.",
  "legal-acts": "Qonunlar, qarorlar va me’yoriy hujjatlar.",
  projects: "Bajarilgan ishlar reestridagi loyihalar.",
  locations: "Xaritada ko‘rsatiladigan loyiha manzillari.",
  clients: "Mijoz tashkilotlar va ularning logotiplari.",
  team: "Rahbariyat va mutaxassislarning profil ma’lumotlari.",
  "staff-certificates": "Xodimlarga tegishli sertifikat va guvohnomalar.",
  credentials: "Tashkilot litsenziyalari, sug‘urta va boshqa hujjatlar.",
  instruments: "Auditda ishlatiladigan o‘lchov asboblari.",
  branches: "Ofis va filiallarning aloqa ma’lumotlari.",
  posts: "Yangiliklar va foydali maqolalar.",
  stats: "Saytda ko‘rinadigan asosiy raqamlar va statistika.",
  leads: "Saytdan yuborilgan mijoz murojaatlari."
};

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { credentials: "same-origin", ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Object.assign(new Error(data.detail || "So‘rov bajarilmadi"), { data, status: response.status });
  return data;
}

function Login({ csrf, onLogin }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    const body = new FormData(event.currentTarget);
    try { onLogin(await api("/login/", { method: "POST", headers: { "X-CSRFToken": csrf }, body })); }
    catch (err) { setError(err.message); setBusy(false); }
  }
  return <main className="login-page"><section className="login-card">
    <div className="login-brand"><img src="/static/core/img/brand-logo.png" alt="TTT AUDIT" /><span>Boshqaruv paneli</span></div>
    <div><p className="eyebrow">Xavfsiz kirish</p><h1>Sayt boshqaruvi</h1><p className="muted">Kontent, loyihalar va murojaatlarni bir joydan boshqaring.</p></div>
    <form onSubmit={submit}><label>Login<input name="username" autoComplete="username" required autoFocus /></label>
      <label>Parol<input name="password" type="password" autoComplete="current-password" required /></label>
      {error && <p className="error">{error}</p>}<button className="primary" disabled={busy}>{busy ? "Tekshirilmoqda…" : "Kirish"}</button></form>
    <a className="site-link" href="/uz/">← Saytga qaytish</a>
  </section></main>;
}

function Field({ field, value }) {
  const common = { name: field.name, required: field.required };
  if (field.type === "boolean") return <label className="check"><input {...common} type="checkbox" defaultChecked={Boolean(value)} /><span>{field.label}</span></label>;
  if (field.type === "textarea") return <label>{field.label}<textarea {...common} defaultValue={value ?? ""} rows={field.name.includes("_uz") ? 5 : 3} />{field.help && <small>{field.help}</small>}</label>;
  if (field.type === "select" || field.type === "multiselect") return <label>{field.label}<select {...common} defaultValue={value ?? (field.type === "multiselect" ? [] : "")} multiple={field.type === "multiselect"}>{field.type !== "multiselect" && <option value="">— Tanlang —</option>}{field.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>{field.help && <small>{field.help}</small>}</label>;
  if (field.type === "file") return <label>{field.label}{value && <span className="file-preview">{field.accept === "image/*" && <img src={value} alt="Joriy rasm" />}<a className="current-file" href={value} target="_blank" rel="noreferrer">Joriy faylni ko‘rish ↗</a></span>}<input {...common} type="file" accept={field.accept} required={false} /></label>;
  const shownValue = field.type === "datetime-local" && value ? String(value).slice(0, 16) : value ?? "";
  return <label>{field.label}<input {...common} type={field.type} defaultValue={shownValue} step={field.type === "number" ? "any" : undefined} />{field.help && <small>{field.help}</small>}</label>;
}

function Editor({ resource, record, csrf, onClose, onSaved, onDeleted }) {
  const [busy, setBusy] = useState(false); const [errors, setErrors] = useState({});
  useEffect(() => {
    const close = event => event.key === "Escape" && !busy && onClose();
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [busy, onClose]);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setErrors({}); const body = new FormData(event.currentTarget);
    resource.schema.forEach(field => { if (field.type === "boolean" && !body.has(field.name)) body.set(field.name, ""); });
    try { const path = record ? `/resources/${resource.key}/${record.id}/` : `/resources/${resource.key}/`; const result = await api(path, { method: "POST", headers: { "X-CSRFToken": csrf }, body }); onSaved(result.record); }
    catch (err) { setErrors(err.data?.errors || { __all__: [{ message: err.message }] }); setBusy(false); }
  }
  async function remove() { if (!confirm("Bu yozuvni butunlay o‘chirasizmi?")) return; setBusy(true); try { await api(`/resources/${resource.key}/${record.id}/`, { method: "DELETE", headers: { "X-CSRFToken": csrf } }); onDeleted(); } catch (err) { setErrors({ __all__: [{ message: err.message }] }); setBusy(false); } }
  return <div className="editor-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}><aside className="editor" aria-modal="true" role="dialog">
    <header><div><p className="eyebrow">{resource.label}</p><h2>{record ? record.label : "Yangi yozuv"}</h2><p className="editor-help">{RESOURCE_GUIDE[resource.key]}</p></div><button type="button" className="icon-btn" onClick={onClose} aria-label="Yopish">×</button></header>
    <form onSubmit={submit}><div className="form-grid">{resource.schema.map(field => <div key={field.name} className={field.type === "textarea" || field.type === "file" ? "wide" : ""}><Field field={field} value={record?.values?.[field.name]} />{errors[field.name]?.map((e,i) => <p className="field-error" key={i}>{e.message}</p>)}</div>)}</div>
      {errors.__all__?.map((e,i) => <p className="error" key={i}>{e.message}</p>)}
      <footer>{record && resource.canDelete && <button type="button" className="danger" onClick={remove} disabled={busy}>O‘chirish</button>}<span /><button type="button" className="secondary" onClick={onClose}>Bekor qilish</button><button className="primary" disabled={busy}>{busy ? "Saqlanmoqda…" : "Saqlash"}</button></footer>
    </form></aside></div>;
}

function Dashboard({ session, onLogout }) {
  const [catalog, setCatalog] = useState([]); const [active, setActive] = useState(null); const [data, setData] = useState(null);
  const [query, setQuery] = useState(""); const [editor, setEditor] = useState(undefined); const [loading, setLoading] = useState(true); const [menu, setMenu] = useState(false);
  const [page, setPage] = useState(1); const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [refresh, setRefresh] = useState(0);
  useEffect(() => { api("/catalog/").then(d => { setCatalog(d.items); setActive(d.items[0]?.key); }).catch(err => setError(err.message)).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!active) return;
    let cancelled = false; setLoading(true); setError("");
    const timer = setTimeout(() => api(`/resources/${active}/?q=${encodeURIComponent(query)}&page=${page}`).then(result => { if (!cancelled) setData(result); }).catch(err => { if (!cancelled) setError(err.message); }).finally(() => { if (!cancelled) setLoading(false); }), 180);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [active, query, page, refresh]);
  const groups = useMemo(() => catalog.reduce((acc, item) => ((acc[item.group] ||= []).push(item), acc), {}), [catalog]);
  const choose = key => { setActive(key); setQuery(""); setPage(1); setMenu(false); setEditor(undefined); setNotice(""); };
  const search = value => { setQuery(value); setPage(1); };
  const reload = async message => {
    try {
      setError("");
      const result = await api(`/resources/${active}/?q=${encodeURIComponent(query)}&page=${page}`);
      setData(result); setCatalog(items => items.map(item => item.key === active ? { ...item, count: result.total } : item)); setNotice(message);
    } catch (err) { setError(err.message); }
  };
  async function logout() { await api("/logout/", { method: "POST", headers: { "X-CSRFToken": session.csrf } }); onLogout(); }
  const current = catalog.find(x => x.key === active);
  return <div className="admin-shell">
    <aside className={`sidebar ${menu ? "is-open" : ""}`}><a className="admin-logo" href="/admin/"><img src="/static/core/img/brand-logo.png" alt="TTT AUDIT" /><span>Admin</span></a><nav>{Object.entries(groups).map(([group, items]) => <section key={group}><h3>{group}</h3>{items.map(item => <button key={item.key} className={active === item.key ? "active" : ""} onClick={() => choose(item.key)}><span>{item.label}</span><b>{item.count}</b></button>)}</section>)}</nav><div className="sidebar-foot"><a href="/uz/" target="_blank">Saytni ochish ↗</a><button onClick={logout}>Chiqish</button></div></aside>
    {menu && <button className="menu-scrim" onClick={() => setMenu(false)} aria-label="Menyuni yopish" />}
    <main className="workspace"><header className="topbar"><button className="mobile-menu" onClick={() => setMenu(true)}>☰</button><div><p className="eyebrow">Boshqaruv paneli</p><h1>{current?.label || "Yuklanmoqda"}</h1></div><div className="user"><span>{session.username.slice(0,1).toUpperCase()}</span><div><b>{session.username}</b><small>Superadmin</small></div></div></header>
      <section className="content"><div className="resource-intro"><div><p className="eyebrow">Bu bo‘lim nima uchun?</p><p>{RESOURCE_GUIDE[active] || "Sayt ma’lumotlarini boshqarish."}</p></div><a href="/uz/" target="_blank" rel="noreferrer">Saytda ko‘rish ↗</a></div>
        {error && <div className="alert alert--error" role="alert"><span>{error}</span><button onClick={() => setRefresh(value => value + 1)}>Qayta urinish</button></div>}
        {notice && <div className="alert alert--success">{notice}</div>}
        <div className="toolbar"><label className="search"><span aria-hidden="true">⌕</span><input value={query} onChange={e => search(e.target.value)} placeholder="Nomi bo‘yicha qidirish…" aria-label="Qidirish" /></label><span className="total">{data?.total ?? 0} ta yozuv</span>{data?.resource.canAdd && <button className="primary" onClick={() => setEditor(null)}>+ Yangi qo‘shish</button>}</div>
        <div className="records">{loading ? <div className="state"><span className="spinner" />Yuklanmoqda…</div> : !data?.records.length ? <div className="state"><b>Ma’lumot topilmadi</b><span>{query ? "Boshqa so‘z bilan qidiring." : "Bu bo‘limga hali yozuv kiritilmagan."}</span></div> : data.records.map((row, i) => <button className="record" key={row.id} onClick={() => setEditor(row)}><span className="record-no">{String((page-1)*40+i+1).padStart(2,"0")}</span><div><b>{row.label || `#${row.id}`}</b><small>Tahrirlash uchun bosing</small></div><span className="arrow">→</span></button>)}</div>
        {data?.pages > 1 && <nav className="pagination" aria-label="Sahifalar"><button className="secondary" disabled={data.page <= 1 || loading} onClick={() => setPage(p => p-1)}>← Oldingi</button><span>{data.page} / {data.pages}-sahifa</span><button className="secondary" disabled={data.page >= data.pages || loading} onClick={() => setPage(p => p+1)}>Keyingi →</button></nav>}
      </section>
    </main>
    {editor !== undefined && data && <Editor resource={data.resource} record={editor} csrf={session.csrf} onClose={() => setEditor(undefined)} onSaved={() => { setEditor(undefined); reload("Ma’lumot muvaffaqiyatli saqlandi."); }} onDeleted={() => { setEditor(undefined); reload("Yozuv o‘chirildi."); }} />}
  </div>;
}

function App() {
  const [session, setSession] = useState(null);
  useEffect(() => { api("/session/").then(setSession); }, []);
  if (!session) return <div className="boot">TTT</div>;
  return session.authenticated ? <Dashboard session={session} onLogout={() => api("/session/").then(setSession)} /> : <Login csrf={session.csrf} onLogin={setSession} />;
}

createRoot(document.getElementById("admin-root")).render(<StrictMode><App /></StrictMode>);
