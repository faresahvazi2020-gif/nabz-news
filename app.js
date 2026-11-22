const DATA_URL = "data/news.json";
const DIGEST_URL = "data/daily_digest.json";
let allNews = [];
let activeCategory = "all";
const $ = s => document.querySelector(s);
const categories = {ai:"هوش مصنوعی و فناوری",security:"امنیتی و نظامی",politics:"سیاست",football:"فوتبال",markets:"بازارها و اقتصاد",crypto:"ارز دیجیتال"};
function faDate(value){if(!value)return "زمان نامشخص";const d=new Date(value);return isNaN(d)?"زمان نامشخص":new Intl.DateTimeFormat("fa-IR",{dateStyle:"medium",timeStyle:"short",timeZone:"Asia/Tehran"}).format(d)}
function safe(s=""){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function render(){
 const q=$("#search").value.trim().toLowerCase();
 const rows=allNews.filter(n=>(activeCategory==="all"||n.category===activeCategory)&&(!q||(n.title+" "+(n.summary||"")+" "+(n.source||"")).toLowerCase().includes(q)));
 $("#news-grid").innerHTML=rows.length?rows.map(n=>`<article class="news-card"><div class="card-top"><span class="category">${safe(categories[n.category]||"خبر")}</span><span class="published">${safe(faDate(n.published))}</span></div><h3>${safe(n.title)}</h3><p>${safe(n.summary||"برای مطالعه جزئیات بیشتر، منبع اصلی خبر را ببینید.")}</p><a class="source-link" href="${safe(n.url)}" target="_blank" rel="noopener noreferrer">مطالعه در ${safe(n.source||"منبع اصلی")} ↗</a></article>`).join(""):'<div class="loading-card">خبری برای نمایش پیدا نشد.</div>';
 $("#empty").classList.toggle("hidden",rows.length>0);
}
async function load(){
 $("#refresh").disabled=true;$("#refresh").innerHTML="↻ <span>در حال دریافت…</span>";
 try{
  const r=await fetch(DATA_URL+"?t="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error("news unavailable");
  const data=await r.json();allNews=data.items||[];$("#updated").textContent=faDate(data.updated_at);render();
 }catch(e){$("#news-grid").innerHTML='<div class="loading-card">داده خبری هنوز منتشر نشده است. پس از اولین اجرای خودکار، خبرها اینجا نمایش داده می‌شوند.</div>'}
 try{
  const r=await fetch(DIGEST_URL+"?t="+Date.now(),{cache:"no-store"});if(r.ok){const d=await r.json();$("#digest-date").textContent=d.date_label||"آخرین گزارش";$("#digest-text").textContent=d.summary||"گزارش روزانه آماده است.";$("#digest-items").innerHTML="<ul>"+(d.highlights||[]).map(x=>`<li>${safe(x.text)} ${x.url?`<a href="${safe(x.url)}" target="_blank" rel="noopener">منبع ↗</a>`:""}</li>`).join("")+"</ul>";}
 }catch(e){}
 $("#refresh").disabled=false;$("#refresh").innerHTML="↻ <span>تازه‌سازی</span>";
}
$("#filters").addEventListener("click",e=>{const b=e.target.closest("button[data-category]");if(!b)return;activeCategory=b.dataset.category;document.querySelectorAll(".filter").forEach(x=>x.classList.toggle("active",x===b));render()});
$("#search").addEventListener("input",render);$("#refresh").addEventListener("click",load);
$("#today").textContent=new Intl.DateTimeFormat("fa-IR",{dateStyle:"full",timeZone:"Asia/Tehran"}).format(new Date());
$("#year").textContent=new Date().getFullYear();load();
setInterval(load,5*60*1000);
