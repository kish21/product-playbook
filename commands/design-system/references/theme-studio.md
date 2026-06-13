# Theme Studio — interactive sample editor (drop-in)

> Loaded by `/design-system` (Step 4). The skill builds the sample, then **injects this block before `</body>`** so a
> non-designer tweaks colour / theme / type-size / responsive **live and AA-guarded**, then **Export** captures the
> finalized tokens → they become `DESIGN.md` §2. **Dev-only — STRIPPED from the real shadcn build** (only the chosen
> tokens persist; the live AA math is the same engine as `frontend-audit/audit.py`).
>
> **The sample must (the skill already enforces these):** define both `:root` (light) + `.dark` token blocks (Law 22);
> size readable text in **rem** with `html { font-size: var(--font-size-base, 16px) }`; use the standard shadcn token
> names (`--background/-foreground/-card/-primary/-primary-foreground/-accent/-accent-foreground/-ring/-border/-radius/-font-sans`).
>
> **AGENT:** replace the `PRESETS` array with **3–5 vetted palettes for the chosen archetype** (from `palettes.md`).

```html
<!-- ===== THEME STUDIO (dev-only; delete this whole block for the production build) ===== -->
<style>
  .ts-open{position:fixed;right:18px;bottom:18px;z-index:2147483640;border:none;border-radius:999px;padding:13px 18px;font:inherit;font-weight:700;font-size:14px;background:var(--primary);color:var(--primary-foreground);cursor:pointer;box-shadow:0 8px 24px oklch(0 0 0 / .25);font-family:var(--font-sans)}
  .ts-open:focus-visible{outline:2px solid var(--ring);outline-offset:2px}
  .ts{position:fixed;right:0;top:0;height:100%;width:330px;max-width:88vw;z-index:2147483646;background:var(--card);border-left:1px solid var(--border);box-shadow:-8px 0 30px oklch(0 0 0 / .2);transform:translateX(100%);transition:transform 160ms ease;overflow:auto;padding:20px;font-family:var(--font-sans);color:var(--foreground)}
  body.ts-on .ts{transform:translateX(0)} body.ts-on .ts-scrim{position:fixed;inset:0;z-index:2147483645;background:oklch(0 0 0 / .35)}
  .ts h3{font-size:17px;font-weight:800} .ts .close{position:absolute;right:14px;top:16px;border:none;background:var(--muted);color:var(--foreground);width:30px;height:30px;border-radius:8px;cursor:pointer;font-size:16px}
  .ts .grp{margin-top:18px} .ts .glab{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted-foreground);margin-bottom:8px}
  .ts .sw{width:38px;height:38px;border-radius:10px;border:2px solid var(--border);cursor:pointer} .ts .swatches{display:flex;gap:8px;flex-wrap:wrap}
  .ts .seg{display:flex;background:var(--muted);border-radius:10px;padding:3px;gap:3px} .ts .seg button{flex:1;border:none;background:transparent;color:var(--muted-foreground);font:inherit;font-weight:600;font-size:13px;padding:8px;border-radius:7px;cursor:pointer}
  .ts .seg button.on{background:var(--card);color:var(--foreground)} .ts .row{display:flex;align-items:center;gap:10px}
  .ts input[type=color]{width:46px;height:34px;border:1px solid var(--border);border-radius:8px;background:none;cursor:pointer} .ts select,.ts input[type=range]{flex:1;font:inherit;font-size:13px;padding:7px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--foreground)}
  .ts .aa{margin-top:8px;background:var(--muted);border-radius:10px;padding:12px;font-size:13px} .ts .aa .line{display:flex;justify-content:space-between;padding:4px 0} .ts .aa .v{font-family:monospace;font-weight:600}
  .ts .pill{font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px} .ts .ok{color:var(--success,oklch(.55 .14 150));background:oklch(.55 .14 150 / .16)} .ts .bad{color:oklch(.55 .2 27);background:oklch(.55 .2 27 / .16)}
  .ts textarea{width:100%;height:110px;margin-top:8px;font-family:monospace;font-size:11px;border:1px solid var(--border);border-radius:8px;padding:10px;background:var(--background);color:var(--foreground)}
  .ts .exp{width:100%;margin-top:8px;border:none;border-radius:8px;padding:10px;font:inherit;font-weight:700;font-size:13px;background:var(--primary);color:var(--primary-foreground);cursor:pointer}
</style>
<button class="ts-open" id="tsOpen">&#127912; Theme Studio</button>
<div class="ts-scrim" id="tsScrim"></div>
<aside class="ts" id="ts" aria-label="Theme studio">
  <h3>Theme Studio</h3><button class="close" id="tsClose" aria-label="Close">&times;</button>
  <div class="grp"><div class="glab">Starter looks</div><div class="swatches" id="presets"></div></div>
  <div class="grp"><div class="glab">Accent</div><div class="row"><input type="color" id="ts_accent" value="#4f46e5" aria-label="Accent colour"><span style="font-size:12px;color:var(--muted-foreground)">Text auto-adjusts for contrast.</span></div></div>
  <div class="grp"><div class="glab">Mode</div><div class="seg" id="ts_mode"><button data-m="light">Light</button><button data-m="dark">Dark</button><button data-m="system">System</button></div></div>
  <div class="grp"><div class="glab">Preview width</div><div class="seg" id="ts_vw"><button data-w="375">Mobile</button><button data-w="768">Tablet</button><button data-w="0" class="on">Desktop</button></div></div>
  <div class="grp"><div class="glab">Base text size</div><div class="seg" id="ts_size"><button data-s="14">14</button><button data-s="15">15</button><button data-s="16" class="on">16</button><button data-s="17">17</button><button data-s="18">18</button></div></div>
  <div class="grp"><div class="glab">Font</div><div class="row"><select id="ts_font"><option value="var(--font-sans)">Default</option><option value='"Plus Jakarta Sans",sans-serif'>Plus Jakarta Sans</option><option value='"Space Grotesk",sans-serif'>Space Grotesk</option><option value='"IBM Plex Sans",sans-serif'>IBM Plex Sans</option></select></div></div>
  <div class="grp"><div class="glab">Roundness</div><div class="row"><input type="range" id="ts_radius" min="0" max="1.6" step="0.05" value="0.6"></div></div>
  <div class="grp"><div class="glab">Accessibility (live WCAG AA)</div><div class="aa"><div class="line"><span>Button text on accent</span><span><span class="v" id="ts_aaBtnV"></span> <span class="pill" id="ts_aaBtnP"></span></span></div><div class="line"><span>Body text on background</span><span><span class="v" id="ts_aaBodyV"></span> <span class="pill" id="ts_aaBodyP"></span></span></div></div></div>
  <div class="grp"><div class="glab">Finalize &rarr; DESIGN.md tokens</div><button class="exp" id="ts_export">Export tokens (light + dark)</button><textarea id="ts_out" readonly placeholder="Click Export to capture the tokens you finalized -> paste into DESIGN.md section 2."></textarea></div>
</aside>
<script>
(function(){
  // OKLCH/hex -> WCAG contrast (same math as audit.py)
  var sl=function(c){c/=255;return c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4)};
  function lh(h){h=h.replace('#','');if(h.length===3)h=h.split('').map(function(c){return c+c}).join('');return .2126*sl(parseInt(h.slice(0,2),16))+.7152*sl(parseInt(h.slice(2,4),16))+.0722*sl(parseInt(h.slice(4,6),16))}
  function lo(L,C,H){var h=H*Math.PI/180,a=C*Math.cos(h),b=C*Math.sin(h),l=L+.3963377774*a+.2158037573*b,m=L-.1055613458*a-.0638541728*b,s=L-.0894841775*a-1.291485548*b;l=l*l*l;m=m*m*m;s=s*s*s;var R=4.0767416621*l-3.3077115913*m+.2309699292*s,G=-1.2684380046*l+2.6097574011*m-.3413193965*s,B=-.0041960863*l-.7034186147*m+1.707614701*s;R=Math.min(1,Math.max(0,R));G=Math.min(1,Math.max(0,G));B=Math.min(1,Math.max(0,B));return .2126*R+.7152*G+.0722*B}
  function lum(v){v=(v||'').trim();var m=v.match(/oklch\(\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)/i);if(m)return lo(+m[1],+m[2],+m[3]);m=v.match(/#([0-9a-fA-F]{3,6})/);if(m)return lh(m[0]);return null}
  function ct(a,b){var x=lum(a),y=lum(b);if(x==null||y==null)return null;var hi=Math.max(x,y),lo2=Math.min(x,y);return (hi+.05)/(lo2+.05)}
  var rs=document.documentElement.style, cs=function(){return getComputedStyle(document.documentElement)};
  function setAccent(v){rs.setProperty('--primary',v);rs.setProperty('--accent',v);rs.setProperty('--ring',v);var L=lum(v),fg=(L!=null&&L>.45)?'oklch(0.20 0.02 265)':'oklch(0.99 0.005 265)';rs.setProperty('--primary-foreground',fg);rs.setProperty('--accent-foreground',fg);aa()}
  function paint(id,r){document.getElementById(id+'V').textContent=r?r.toFixed(2)+':1':'-';var p=document.getElementById(id+'P'),ok=r&&r>=4.5;p.textContent=ok?'AA':(r&&r>=3?'large':'FAIL');p.className='pill '+(ok?'ok':'bad')}
  function aa(){var c=cs();paint('ts_aaBtn',ct(c.getPropertyValue('--primary-foreground'),c.getPropertyValue('--primary')));paint('ts_aaBody',ct(c.getPropertyValue('--foreground'),c.getPropertyValue('--background')))}
  // AGENT: replace with 3-5 vetted palettes for this archetype (from palettes.md)
  var PRESETS=[['Indigo','oklch(0.52 0.16 265)'],['Coral','oklch(0.58 0.20 25)'],['Emerald','oklch(0.55 0.15 155)'],['Violet','oklch(0.55 0.22 300)'],['Amber','oklch(0.74 0.15 75)']];
  var pc=document.getElementById('presets');PRESETS.forEach(function(p){var b=document.createElement('button');b.className='sw';b.title=p[0];b.style.background=p[1];b.onclick=function(){setAccent(p[1])};pc.appendChild(b)});
  document.getElementById('ts_accent').addEventListener('input',function(e){setAccent(e.target.value)});
  document.getElementById('ts_font').addEventListener('change',function(e){rs.setProperty('--font-sans',e.target.value)});
  document.getElementById('ts_radius').addEventListener('input',function(e){rs.setProperty('--radius',e.target.value+'rem')});
  function seg(id,fn){var el=document.getElementById(id);el.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;[].forEach.call(el.children,function(x){x.classList.remove('on')});b.classList.add('on');fn(b)})}
  seg('ts_mode',function(b){var el=document.documentElement,m=b.dataset.m;el.classList.remove('dark');el.classList.remove('light');if(m==='dark')el.classList.add('dark');else if(m==='light')el.classList.add('light');aa()});
  seg('ts_vw',function(b){var st=document.getElementById('ts_stage')||document.body;var w=+b.dataset.w;if(w){st.style.maxWidth=w+'px';st.style.margin='14px auto';st.style.border='1px solid var(--border)';st.style.borderRadius='20px';st.style.overflow='hidden'}else{st.style.maxWidth='';st.style.border='';st.style.borderRadius='';st.style.margin=''}});
  seg('ts_size',function(b){rs.setProperty('--font-size-base',b.dataset.s+'px')});
  var body=document.body;document.getElementById('tsOpen').onclick=function(){body.classList.add('ts-on')};document.getElementById('tsClose').onclick=function(){body.classList.remove('ts-on')};document.getElementById('tsScrim').onclick=function(){body.classList.remove('ts-on')};
  document.addEventListener('keydown',function(e){if(e.key==='Escape')body.classList.remove('ts-on')});
  // sync the Mode toggle to the page's ACTUAL starting mode (.dark / .light / neither = System) — so a
  // dark-default product opens on "Dark", not a hard-coded "Light" (T5-6).
  (function(){var el=document.documentElement,m=el.classList.contains('dark')?'dark':el.classList.contains('light')?'light':'system';var sg=document.getElementById('ts_mode');[].forEach.call(sg.children,function(b){b.classList.toggle('on',b.dataset.m===m)})})();
  var KEYS=['--background','--foreground','--card','--card-foreground','--muted','--muted-foreground','--primary','--primary-foreground','--accent','--accent-foreground','--border','--ring','--radius','--font-size-base','--font-sans'];
  document.getElementById('ts_export').onclick=function(){var el=document.documentElement,was=el.classList.contains('dark');function rd(){var c=cs();return KEYS.map(function(k){return '  '+k+': '+c.getPropertyValue(k).trim()+';'}).join('\n')}el.classList.remove('dark');var L=rd();el.classList.add('dark');var D=rd();if(!was)el.classList.remove('dark');document.getElementById('ts_out').value=':root {\n'+L+'\n}\n.dark {\n'+D+'\n}\n'};
  aa();
})();
</script>
<!-- ===== /THEME STUDIO ===== -->
```

## Notes
- **Responsive preview (T5-1 — required for the width buttons to actually reflow):** wrap the page content in
  `<div id="ts_stage" style="container-type:inline-size">…</div>` **and write the page's responsive layout with
  `@container` queries, NOT `@media`.** `@media` reacts to the *window*, not the box the toggle resizes — so with `@media`
  the Mobile/Tablet buttons just shrink a strip of the desktop layout (misleading). Keep `@media` only for viewport-true
  things (`prefers-reduced-motion`, `prefers-color-scheme`).
- **Mode + the OS (T5-6):** the studio sets a `.light`/`.dark` class (or neither = System). The sample MUST use the
  escape-hatch dark pattern (`design-md-template.md` §2: `:root:not(.light){…}` for system-dark) or a manual "Light" can't
  beat an OS set to dark. **The Mode toggle auto-reflects the page's starting mode on load** — a **dark-default**
  product ships `<html class="dark">` and the toggle opens on **Dark** (not a hard-coded Light). Keep the sample
  **token-only (no hardcoded colours)** so switching to Light actually adapts — a stray `#fff` will ghost in light mode.
- **Font in a standalone preview (T5-7):** load the distinctive face via `<link>` (the laws forbid CSS `@import`); the real
  shadcn/Next build uses self-hosted `next/font`. Without it the preview silently falls back to a system font.
- **Base text size** sets `--font-size-base`; the sample's `html { font-size: var(--font-size-base,16px) }` + rem text
  makes the whole type scale respond. Export captures it as a token (so DESIGN.md is complete).
- **Export** writes BOTH `:root` and `.dark` blocks → drop straight into `DESIGN.md` §2 / shadcn `globals.css`.
- Strip the entire commented block for production; the chosen tokens already live in `DESIGN.md`.
- The block is delimited by the `THEME STUDIO … /THEME STUDIO` markers; **`/frontend-audit` skips everything between
  them** (it's dev-only), so the studio's own colour-input hex literal + 🎨 emoji + panel labels don't false-positive.
