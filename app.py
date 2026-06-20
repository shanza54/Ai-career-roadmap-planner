import gradio as gr
from groq import Groq
import os
import json
import re
from fpdf import FPDF

# =============================================================================
# INIT
# =============================================================================
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# =============================================================================
# ROADMAP GENERATOR  →  returns structured JSON
# =============================================================================
ROADMAP_JSON_PROMPT = """
You are a structured data generator. Return ONLY valid JSON — no markdown fences, no explanation.

Generate a career roadmap with this exact schema:
{{
  "title": "<roadmap title>",
  "summary": "<2-sentence overview>",
  "total_weeks": <number>,
  "milestones": [
    {{
      "id": 1,
      "week_range": "Week 1-2",
      "title": "<milestone title>",
      "topics": ["topic1", "topic2", "topic3"],
      "project": "<hands-on mini project description>",
      "resources": [
        {{
          "name": "<resource name>",
          "type": "Video | Docs | Course | Book | Tool",
          "url": "<real URL>"
        }}
      ]
    }}
  ]
}}

Rules:
- Create exactly {num_milestones} milestones spread across {months} months.
- Each milestone must have 2-4 real, clickable resources (YouTube search URLs are fine: https://www.youtube.com/results?search_query=...).
- Use real documentation links where possible (pytorch.org, scikit-learn.org, docs.python.org, etc.).
- Projects must be concrete and buildable.

Domain: {domain}
Current Level: {level}
Hours per day available: {hours}
Duration: {months} months
"""

def generate_roadmap(domain, level, hours, months):
    """Call Groq and return (json_data, error_string)."""
    num_milestones = max(3, min(int(months) * 2, 12))
    prompt = ROADMAP_JSON_PROMPT.format(
        domain=domain, level=level, hours=hours,
        months=months, num_milestones=num_milestones
    )
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON. No markdown, no backticks."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}\n\nRaw response:\n{raw[:800]}"
    except Exception as e:
        return None, f"API Error: {str(e)}"


# =============================================================================
# BUILD TIMELINE HTML
# =============================================================================
def build_timeline_html(data: dict) -> str:
    milestones = data.get("milestones", [])
    title      = data.get("title", "Your Roadmap")
    summary    = data.get("summary", "")

    nodes_html = ""
    for i, m in enumerate(milestones):
        resources_html = "".join(
            f'<a href="{r["url"]}" target="_blank" class="res-chip res-{r["type"].lower().split()[0]}">'
            f'{r["type"]} &middot; {r["name"]}</a>'
            for r in m.get("resources", [])
        )
        topics_html = "".join(f"<span class='topic-tag'>{t}</span>" for t in m.get("topics", []))
        side = "left" if i % 2 == 0 else "right"

        nodes_html += f"""
        <div class="tl-item {side}" data-id="{m['id']}">
          <div class="tl-dot" title="{m['title']}">
            <span class="dot-num">{m['id']}</span>
          </div>
          <div class="tl-card" onclick="toggleCard(this)">
            <div class="card-header">
              <span class="week-badge">{m['week_range']}</span>
              <h3 class="card-title">{m['title']}</h3>
            </div>
            <div class="card-body">
              <div class="topics-row">{topics_html}</div>
              <div class="project-box">
                <span class="proj-label">Project</span>
                <p>{m.get('project','')}</p>
              </div>
              <div class="resources-row">{resources_html}</div>
            </div>
          </div>
        </div>
        """

    return f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap');
  #tl-root {{
    font-family:'Inter',sans-serif;
    background:#0D0D1A;
    color:#E2E8F0;
    padding:2rem 1rem 3rem;
    border-radius:16px;
    position:relative;
    overflow:hidden;
  }}
  #tl-root::before {{
    content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse at 20% 0%,rgba(99,102,241,.15) 0%,transparent 60%),
               radial-gradient(ellipse at 80% 100%,rgba(168,85,247,.12) 0%,transparent 60%);
    pointer-events:none;
  }}
  .tl-header{{text-align:center;margin-bottom:2.5rem;position:relative;z-index:1;}}
  .tl-header h2{{
    font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;
    background:linear-gradient(135deg,#818CF8,#C084FC);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 .5rem;
  }}
  .tl-header p{{color:#94A3B8;font-size:.95rem;max-width:600px;margin:auto;}}
  .tl-spine{{position:relative;max-width:860px;margin:auto;padding:0 0 2rem;}}
  .tl-spine::before{{
    content:'';position:absolute;left:50%;top:0;bottom:0;width:2px;
    background:linear-gradient(to bottom,#6366F1,#A855F7,#6366F1);
    transform:translateX(-50%);
  }}
  .tl-item{{display:flex;justify-content:flex-end;padding:0 calc(50% + 28px) 2.5rem 0;position:relative;}}
  .tl-item.right{{justify-content:flex-start;padding:0 0 2.5rem calc(50% + 28px);}}
  .tl-dot{{
    position:absolute;left:50%;top:18px;transform:translateX(-50%);
    width:42px;height:42px;border-radius:50%;
    background:linear-gradient(135deg,#6366F1,#A855F7);
    display:flex;align-items:center;justify-content:center;z-index:2;
    box-shadow:0 0 0 4px #0D0D1A,0 0 16px rgba(99,102,241,.6);
    transition:box-shadow .2s;
  }}
  .tl-dot:hover{{box-shadow:0 0 0 4px #0D0D1A,0 0 28px rgba(168,85,247,.9);}}
  .dot-num{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:.9rem;color:#fff;}}
  .tl-card{{
    background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
    border-radius:12px;padding:1rem 1.1rem;max-width:340px;width:100%;
    cursor:pointer;transition:background .2s,transform .15s,border-color .2s;
  }}
  .tl-card:hover{{background:rgba(255,255,255,.07);border-color:rgba(99,102,241,.5);transform:translateY(-2px);}}
  .card-header{{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:.5rem;}}
  .week-badge{{
    background:rgba(99,102,241,.25);color:#A5B4FC;
    border-radius:999px;padding:2px 10px;font-size:.72rem;font-weight:600;white-space:nowrap;
  }}
  .card-title{{font-family:'Space Grotesk',sans-serif;font-size:.95rem;font-weight:600;color:#E2E8F0;margin:0;}}
  .card-body{{display:none;margin-top:.75rem;border-top:1px solid rgba(255,255,255,.07);padding-top:.75rem;}}
  .card-body.open{{display:block;}}
  .topics-row{{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.75rem;}}
  .topic-tag{{background:rgba(168,85,247,.15);color:#D8B4FE;border-radius:6px;padding:2px 8px;font-size:.73rem;}}
  .project-box{{
    background:rgba(16,185,129,.08);border-left:3px solid #10B981;
    border-radius:0 8px 8px 0;padding:.5rem .75rem;margin-bottom:.75rem;
  }}
  .proj-label{{font-size:.72rem;font-weight:600;color:#6EE7B7;display:block;margin-bottom:.2rem;}}
  .project-box p{{margin:0;font-size:.82rem;color:#CBD5E1;line-height:1.5;}}
  .resources-row{{display:flex;flex-wrap:wrap;gap:.4rem;}}
  .res-chip{{display:inline-block;border-radius:6px;padding:3px 9px;font-size:.72rem;font-weight:500;text-decoration:none;transition:opacity .15s;}}
  .res-chip:hover{{opacity:.75;}}
  .res-video{{background:rgba(239,68,68,.15);color:#FCA5A5;}}
  .res-docs{{background:rgba(59,130,246,.15);color:#93C5FD;}}
  .res-course{{background:rgba(245,158,11,.15);color:#FCD34D;}}
  .res-book{{background:rgba(16,185,129,.15);color:#6EE7B7;}}
  .res-tool{{background:rgba(139,92,246,.15);color:#C4B5FD;}}
  @media(max-width:640px){{
    .tl-spine::before{{left:20px;}}
    .tl-item,.tl-item.right{{justify-content:flex-start;padding:0 0 2rem 52px;}}
    .tl-dot{{left:20px;}}
    .tl-card{{max-width:100%;}}
  }}
</style>
<div id="tl-root">
  <div class="tl-header">
    <h2>&#128506; {title}</h2>
    <p>{summary}</p>
  </div>
  <div class="tl-spine">
    {nodes_html}
  </div>
</div>
<script>
function toggleCard(card){{
  var body=card.querySelector('.card-body');
  if(body) body.classList.toggle('open');
}}
window.addEventListener('load',function(){{
  var first=document.querySelector('.tl-card .card-body');
  if(first) first.classList.add('open');
}});
</script>
"""


# =============================================================================
# CHECKLIST + PROGRESS
# =============================================================================
def extract_checklist(data: dict):
    return [f"[{m['week_range']}] {m['title']}" for m in data.get("milestones", [])]

def build_progress_html(completed: int, total: int) -> str:
    if total == 0:
        pct = 0
    else:
        pct = round((completed / total) * 100)
    color = "#6366F1" if pct < 50 else "#A855F7" if pct < 80 else "#10B981"
    label = "Keep going! 💪" if pct < 30 else "Great progress! 🔥" if pct < 70 else "Almost there! 🚀" if pct < 100 else "Complete! 🎉"
    return f"""
<div style="font-family:'Inter',sans-serif;padding:.75rem 1rem;
            background:#0D0D1A;border-radius:12px;border:1px solid rgba(255,255,255,.08);">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">
    <span style="font-weight:600;color:#E2E8F0;">Overall Progress</span>
    <span style="color:{color};font-weight:700;font-size:1.05rem;">{pct}% — {label}</span>
  </div>
  <div style="background:rgba(255,255,255,.07);border-radius:999px;height:12px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;border-radius:999px;
                background:linear-gradient(90deg,#6366F1,{color});transition:width .4s ease;"></div>
  </div>
  <div style="margin-top:.4rem;color:#64748B;font-size:.8rem;">
    {completed} of {total} milestones completed
  </div>
</div>
"""


# =============================================================================
# PDF EXPORT
# =============================================================================
def download_pdf(roadmap_json_str: str) -> str:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    try:
        data = json.loads(roadmap_json_str)
    except Exception:
        data = {"title": "Roadmap", "summary": roadmap_json_str, "milestones": []}

    def safe(text):
        return str(text).encode("latin-1", "ignore").decode("latin-1")

    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 12, safe(data.get("title", "Career Roadmap")), ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 7, safe(data.get("summary", "")))
    pdf.ln(5)

    for m in data.get("milestones", []):
        pdf.set_fill_color(240, 240, 255)
        pdf.set_text_color(50, 50, 200)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 9, safe(f"  {m['week_range']}  --  {m['title']}"), ln=True, fill=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "Topics:", ln=True)
        pdf.set_font("Arial", "", 10)
        for t in m.get("topics", []):
            pdf.cell(0, 6, safe(f"  * {t}"), ln=True)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "Project:", ln=True)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, safe(f"  {m.get('project','')}"))
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "Resources:", ln=True)
        pdf.set_font("Arial", "", 9)
        for r in m.get("resources", []):
            pdf.set_text_color(30, 100, 200)
            pdf.multi_cell(0, 5, safe(f"  [{r['type']}] {r['name']}  ->  {r['url']}"))
        pdf.set_text_color(30, 30, 30)
        pdf.ln(4)

    path = "roadmap.pdf"
    pdf.output(path)
    return path


# =============================================================================
# CSS
# =============================================================================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
body, .gradio-container {
    background:#080812 !important;
    font-family:'Inter',sans-serif !important;
}
.gradio-container { max-width:1100px !important; margin:auto !important; }
.gen-btn {
    background:linear-gradient(135deg,#6366F1,#A855F7) !important;
    color:white !important; font-weight:700 !important;
    font-family:'Space Grotesk',sans-serif !important;
    border-radius:10px !important; border:none !important;
    font-size:1rem !important; transition:opacity .2s,transform .15s !important;
}
.gen-btn:hover { opacity:.9 !important; transform:translateY(-1px) !important; }
.sec-btn {
    background:rgba(99,102,241,.15) !important; color:#818CF8 !important;
    border:1px solid rgba(99,102,241,.3) !important; border-radius:8px !important;
    font-weight:600 !important; transition:background .2s !important;
}
.sec-btn:hover { background:rgba(99,102,241,.28) !important; }
input, textarea, select {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(255,255,255,.1) !important;
    color:#E2E8F0 !important; border-radius:8px !important;
}
label { color:#94A3B8 !important; font-size:.85rem !important; }
.checkbox-group label { color:#CBD5E1 !important; font-size:.88rem !important; }
"""

# =============================================================================
# GRADIO UI
# =============================================================================
with gr.Blocks(title="AI Career & Skill Path Planner", css=custom_css) as app:

    roadmap_data     = gr.State(value=None)
    roadmap_json_str = gr.Textbox(visible=False, value="")

    gr.HTML("""
    <div style="text-align:center;padding:2rem 1rem 1.5rem;">
      <h1 style="font-family:'Space Grotesk',sans-serif;font-size:2.2rem;font-weight:700;
                 background:linear-gradient(135deg,#818CF8,#C084FC);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 .4rem;">
        AI Career &amp; Skill Path Planner
      </h1>
      <p style="color:#64748B;font-size:.95rem;margin:0;">
        Visual, interactive roadmaps with real resources — track your progress milestone by milestone.
      </p>
    </div>
    """)

    with gr.Row():
        domain = gr.Textbox(
            label="What do you want to learn?",
            placeholder="e.g. Machine Learning, Flutter Dev, Cybersecurity…",
            scale=3
        )
        level = gr.Dropdown(
            ["Beginner", "Intermediate", "Advanced"],
            value="Beginner", label="Current Level", scale=1
        )
    with gr.Row():
        hours  = gr.Slider(1, 10, value=2, step=1, label="Hours per day")
        months = gr.Slider(1, 12, value=3, step=1, label="Months available")

    gen_btn = gr.Button("Generate My Roadmap", elem_classes=["gen-btn"])

    progress_html = gr.HTML(build_progress_html(0, 0))

    timeline_html = gr.HTML("""
    <div style="text-align:center;padding:3rem;color:#475569;
                border:1px dashed rgba(255,255,255,.08);border-radius:12px;
                font-family:'Space Grotesk',sans-serif;">
      Fill in the fields above and click Generate to see your interactive roadmap.
    </div>""")

    gr.HTML("<hr style='border:none;border-top:1px solid rgba(255,255,255,.06);margin:1.5rem 0;'>")

    gr.HTML("""
    <h3 style="font-family:'Space Grotesk',sans-serif;color:#818CF8;
                margin:0 0 .75rem;font-size:1rem;">
      Mark milestones you have completed
    </h3>""")
    checklist = gr.CheckboxGroup(choices=[], label="", interactive=True)

    with gr.Row():
        pdf_btn  = gr.Button("Download as PDF", elem_classes=["sec-btn"])
        pdf_file = gr.File(label="")

    # ── EVENT: Generate ──────────────────────────────────────────────────────
    def on_generate(domain_val, level_val, hours_val, months_val):
        data, err = generate_roadmap(domain_val, level_val, hours_val, months_val)
        if err or data is None:
            err_html = f"""<div style="padding:2rem;background:rgba(239,68,68,.1);
                border:1px solid rgba(239,68,68,.3);border-radius:12px;
                color:#FCA5A5;font-family:'Inter',sans-serif;">Error: {err}</div>"""
            return err_html, gr.update(choices=[], value=[]), build_progress_html(0, 0), None, ""
        timeline  = build_timeline_html(data)
        choices   = extract_checklist(data)
        prog_html = build_progress_html(0, len(choices))
        json_str  = json.dumps(data)
        return timeline, gr.update(choices=choices, value=[]), prog_html, data, json_str

    gen_btn.click(
        fn=on_generate,
        inputs=[domain, level, hours, months],
        outputs=[timeline_html, checklist, progress_html, roadmap_data, roadmap_json_str],
        show_progress="full"
    )

    # ── EVENT: Checklist → progress bar ─────────────────────────────────────
    def on_checklist_change(checked, data):
        total = len(data.get("milestones", [])) if data else 0
        return build_progress_html(len(checked), total)

    checklist.change(
        fn=on_checklist_change,
        inputs=[checklist, roadmap_data],
        outputs=progress_html
    )

    # ── EVENT: PDF download ──────────────────────────────────────────────────
    pdf_btn.click(fn=download_pdf, inputs=roadmap_json_str, outputs=pdf_file)


# =============================================================================
if __name__ == "__main__":
    app.launch(debug=True)