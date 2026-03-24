const pptxgen = require("/Users/jackeyw/.nvm/versions/node/v20.19.5/lib/node_modules/pptxgenjs");

// ─── Theme colors (no # prefix) ───────────────────────────────────────────────
const C = {
  bg:        "1a1a2e",   // dark navy background
  bgLight:   "16213e",   // slightly lighter dark
  panel:     "0f3460",   // deep blue panel
  panelDark: "162447",   // darker panel
  green:     "76B900",   // NVIDIA green
  greenDim:  "4a7300",   // darker green
  white:     "FFFFFF",
  offWhite:  "E8E8E8",
  muted:     "9CA3AF",
  accent:    "00D4FF",   // cyan accent for variety
  cardBg:    "1e2a4a",   // card background
};

async function buildPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author  = "Jackey Wang";
  pres.title   = "J-Bot (Everyone's Jarvis) — Claude Code in Your Teams Chat";

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 1 — Title
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Full-width gradient-style bottom strip
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 4.8, w: 10, h: 0.825,
      fill: { color: C.green },
      line: { color: C.green },
    });

    // Decorative large circle (top-right, partially off-screen)
    s.addShape(pres.shapes.OVAL, {
      x: 7.5, y: -1.2, w: 4, h: 4,
      fill: { color: C.panel },
      line: { color: C.panel },
    });

    // Smaller accent circle
    s.addShape(pres.shapes.OVAL, {
      x: -0.8, y: 3.5, w: 2.5, h: 2.5,
      fill: { color: C.panelDark },
      line: { color: C.panelDark },
    });

    // Robot emoji / title icon area — green circle
    s.addShape(pres.shapes.OVAL, {
      x: 0.55, y: 1.0, w: 1.1, h: 1.1,
      fill: { color: C.green },
      line: { color: C.green },
    });

    // Emoji label inside circle
    s.addText("🤖", {
      x: 0.55, y: 1.0, w: 1.1, h: 1.1,
      fontSize: 30, align: "center", valign: "middle",
      margin: 0,
    });

    // Main title
    s.addText("J-Bot", {
      x: 1.8, y: 0.9, w: 7.5, h: 1.2,
      fontSize: 60, bold: true, color: C.white,
      fontFace: "Arial Black",
      align: "left", valign: "middle",
      margin: 0,
    });

    // Subtitle
    s.addText("Everyone's Jarvis — Claude Code in Your Teams Chat", {
      x: 1.8, y: 2.05, w: 7.5, h: 0.65,
      fontSize: 22, color: C.green,
      fontFace: "Calibri",
      align: "left", valign: "top",
      margin: 0, bold: false,
    });

    // Tagline
    s.addText("Zero context switching. Full Claude Code power.", {
      x: 1.8, y: 2.7, w: 7.5, h: 0.5,
      fontSize: 16, color: C.offWhite,
      fontFace: "Calibri",
      align: "left", valign: "top",
      italic: true, margin: 0,
    });

    // Footer text on green bar
    s.addText("NVIDIA Interconnect Shanghai  |  March 2026", {
      x: 0, y: 4.8, w: 10, h: 0.825,
      fontSize: 13, color: C.bg,
      fontFace: "Calibri",
      align: "center", valign: "middle",
      bold: true, margin: 0,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 2 — The Problem
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625,
      fill: { color: C.green }, line: { color: C.green },
    });

    // Title
    s.addText("The Challenge", {
      x: 0.35, y: 0.35, w: 9.3, h: 0.7,
      fontSize: 36, bold: true, color: C.white,
      fontFace: "Arial Black", align: "left", valign: "top", margin: 0,
    });

    // Subtitle
    s.addText("Why engineers need a better way to work with AI", {
      x: 0.35, y: 1.0, w: 9.3, h: 0.4,
      fontSize: 15, color: C.green, fontFace: "Calibri",
      align: "left", valign: "top", italic: true, margin: 0,
    });

    // Problem items — 4 cards in a 2x2 layout
    const problems = [
      {
        icon: "⇌",
        title: "Context Switching",
        body: "Engineers constantly switch between terminal and Teams, breaking deep focus",
      },
      {
        icon: "🔒",
        title: "Isolated Sessions",
        body: "Claude Code sessions are siloed — no team visibility into what's running",
      },
      {
        icon: "📋",
        title: "Manual Copy-Paste",
        body: "Results must be manually copied and shared with colleagues every time",
      },
      {
        icon: "💭",
        title: "No Persistent Context",
        body: "Each conversation starts fresh — no memory of previous work or decisions",
      },
    ];

    const cols = [0.35, 5.15];
    const rows = [1.6, 3.3];

    problems.forEach((p, i) => {
      const cx = cols[i % 2];
      const cy = rows[Math.floor(i / 2)];
      const cw = 4.5;
      const ch = 1.55;

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: ch,
        fill: { color: C.cardBg },
        line: { color: C.panel },
        shadow: { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.3 },
      });

      // Green left accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 0.06, h: ch,
        fill: { color: C.green }, line: { color: C.green },
      });

      // Icon
      s.addText(p.icon, {
        x: cx + 0.15, y: cy + 0.12, w: 0.6, h: 0.6,
        fontSize: 22, align: "center", valign: "middle", margin: 0,
      });

      // Title
      s.addText(p.title, {
        x: cx + 0.82, y: cy + 0.1, w: cw - 0.95, h: 0.38,
        fontSize: 14, bold: true, color: C.white,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      // Body
      s.addText(p.body, {
        x: cx + 0.82, y: cy + 0.5, w: cw - 0.95, h: 0.9,
        fontSize: 12, color: C.offWhite,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 3 — The Solution
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Top green header band
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 1.15,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("Meet J-Bot", {
      x: 0.4, y: 0, w: 9.2, h: 1.15,
      fontSize: 38, bold: true, color: C.bg,
      fontFace: "Arial Black", align: "left", valign: "middle", margin: 0,
    });

    // Center callout box
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.2, y: 1.35, w: 7.6, h: 0.85,
      fill: { color: C.panel }, line: { color: C.accent },
    });

    s.addText("Type  @jbot  in any Teams group chat", {
      x: 1.2, y: 1.35, w: 7.6, h: 0.85,
      fontSize: 22, bold: true, color: C.accent,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    // Main value prop
    s.addText("AI-powered coding assistant that lives where your team already works", {
      x: 0.5, y: 2.35, w: 9, h: 0.6,
      fontSize: 17, color: C.offWhite,
      fontFace: "Calibri", align: "center", valign: "top", margin: 0,
    });

    // Three value pillars
    const pillars = [
      { icon: "⚡", label: "Zero Setup", desc: "No new tools to learn. Works in existing Teams channels." },
      { icon: "🧠", label: "Full Claude Power", desc: "Complete Claude Code capabilities via @jbot trigger." },
      { icon: "👥", label: "Team Visibility", desc: "Everyone sees progress and results in real time." },
    ];

    pillars.forEach((p, i) => {
      const px = 0.35 + i * 3.18;
      const py = 3.1;
      const pw = 3.0;
      const ph = 2.1;

      s.addShape(pres.shapes.RECTANGLE, {
        x: px, y: py, w: pw, h: ph,
        fill: { color: C.cardBg }, line: { color: C.panelDark },
      });

      // Top green strip on each card
      s.addShape(pres.shapes.RECTANGLE, {
        x: px, y: py, w: pw, h: 0.06,
        fill: { color: C.green }, line: { color: C.green },
      });

      s.addText(p.icon, {
        x: px, y: py + 0.12, w: pw, h: 0.65,
        fontSize: 28, align: "center", valign: "middle", margin: 0,
      });

      s.addText(p.label, {
        x: px + 0.15, y: py + 0.8, w: pw - 0.3, h: 0.4,
        fontSize: 15, bold: true, color: C.green,
        fontFace: "Calibri", align: "center", margin: 0,
      });

      s.addText(p.desc, {
        x: px + 0.15, y: py + 1.22, w: pw - 0.3, h: 0.8,
        fontSize: 12, color: C.offWhite,
        fontFace: "Calibri", align: "center", valign: "top", margin: 0,
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 4 — Architecture
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("Two-Tier Architecture", {
      x: 0.35, y: 0.25, w: 9.3, h: 0.65,
      fontSize: 36, bold: true, color: C.white,
      fontFace: "Arial Black", align: "left", valign: "top", margin: 0,
    });

    // Flow row: Teams → Poller → Manager → Workers → Chat
    // Draw as a horizontal process flow with arrows

    const flowItems = [
      { label: "Teams\nChat", color: C.panel },
      { label: "Poller", color: C.panelDark },
      { label: "Manager\n(Persistent)", color: C.green },
      { label: "Workers\n(On-demand)", color: "005599" },
      { label: "Results\nto Chat", color: C.panel },
    ];

    const startX = 0.35;
    const boxW   = 1.55;
    const boxH   = 1.0;
    const gapX   = 0.28;
    const rowY   = 1.1;

    flowItems.forEach((item, i) => {
      const bx = startX + i * (boxW + gapX);

      s.addShape(pres.shapes.RECTANGLE, {
        x: bx, y: rowY, w: boxW, h: boxH,
        fill: { color: item.color }, line: { color: item.color },
      });

      s.addText(item.label, {
        x: bx, y: rowY, w: boxW, h: boxH,
        fontSize: 13, bold: true, color: C.bg,
        fontFace: "Calibri", align: "center", valign: "middle", margin: 4,
      });

      // Arrow (except after last item)
      if (i < flowItems.length - 1) {
        const ax = bx + boxW;
        s.addShape(pres.shapes.LINE, {
          x: ax, y: rowY + boxH / 2, w: gapX, h: 0,
          line: { color: C.green, width: 2 },
        });
        // Arrowhead as small triangle text
        s.addText("▶", {
          x: ax + gapX - 0.18, y: rowY + boxH / 2 - 0.15, w: 0.22, h: 0.3,
          fontSize: 10, color: C.green, align: "center", valign: "middle", margin: 0,
        });
      }
    });

    // Manager details box
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.35, y: 2.42, w: 4.55, h: 2.85,
      fill: { color: C.cardBg }, line: { color: C.green },
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.35, y: 2.42, w: 4.55, h: 0.42,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("Manager  (Persistent)", {
      x: 0.35, y: 2.42, w: 4.55, h: 0.42,
      fontSize: 14, bold: true, color: C.bg,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    const managerFeatures = [
      "Remembers full conversation context",
      "Routes tasks to available workers",
      "Makes architectural decisions",
      "Enforces role-based permissions",
      "Tracks costs per session",
    ];

    s.addText(managerFeatures.map((f, i) => ({
      text: f,
      options: { bullet: true, breakLine: i < managerFeatures.length - 1, fontSize: 13, color: C.offWhite },
    })), {
      x: 0.55, y: 2.9, w: 4.2, h: 2.2,
      fontFace: "Calibri",
    });

    // Workers details box
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.15, y: 2.42, w: 4.5, h: 2.85,
      fill: { color: C.cardBg }, line: { color: C.accent },
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.15, y: 2.42, w: 4.5, h: 0.42,
      fill: { color: "005599" }, line: { color: "005599" },
    });

    s.addText("Workers  (On-demand)", {
      x: 5.15, y: 2.42, w: 4.5, h: 0.42,
      fontSize: 14, bold: true, color: C.white,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    const workerFeatures = [
      "Execute tasks with full Claude Code",
      "Up to 5 concurrent sessions",
      "60-second heartbeat progress updates",
      "Isolated per task — no cross-contamination",
      "Spin up on demand, tear down on completion",
    ];

    s.addText(workerFeatures.map((f, i) => ({
      text: f,
      options: { bullet: true, breakLine: i < workerFeatures.length - 1, fontSize: 13, color: C.offWhite },
    })), {
      x: 5.35, y: 2.9, w: 4.1, h: 2.2,
      fontFace: "Calibri",
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 5 — Key Features (2x3 grid)
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Top header
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 1.0,
      fill: { color: C.panelDark }, line: { color: C.panelDark },
    });

    s.addText("Core Capabilities", {
      x: 0.4, y: 0, w: 9.2, h: 1.0,
      fontSize: 36, bold: true, color: C.white,
      fontFace: "Arial Black", align: "left", valign: "middle", margin: 0,
    });

    const features = [
      { icon: "💬", title: "Teams-Native", desc: "@jbot trigger in any group chat. No separate tools." },
      { icon: "🧠", title: "Stateful Manager", desc: "Persistent memory across all interactions and sessions." },
      { icon: "⚡", title: "Concurrent Workers", desc: "Up to 5 parallel task sessions run simultaneously." },
      { icon: "📡", title: "Real-time Progress", desc: "60-second heartbeat updates appear directly in chat." },
      { icon: "🔐", title: "Permission Control", desc: "Admin vs member role enforcement built in." },
      { icon: "💰", title: "Cost Tracking", desc: "Per-session USD cost monitoring and reporting." },
    ];

    const cols = [0.2, 3.5, 6.8];
    const rows = [1.15, 3.25];
    const cw = 3.0;
    const ch = 1.85;

    features.forEach((f, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cx = cols[col];
      const cy = rows[row];

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: ch,
        fill: { color: C.cardBg }, line: { color: C.panelDark },
        shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.25 },
      });

      // Top green accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: 0.06,
        fill: { color: C.green }, line: { color: C.green },
      });

      // Icon circle
      s.addShape(pres.shapes.OVAL, {
        x: cx + 0.15, y: cy + 0.15, w: 0.55, h: 0.55,
        fill: { color: C.panel }, line: { color: C.panel },
      });

      s.addText(f.icon, {
        x: cx + 0.15, y: cy + 0.15, w: 0.55, h: 0.55,
        fontSize: 16, align: "center", valign: "middle", margin: 0,
      });

      s.addText(f.title, {
        x: cx + 0.82, y: cy + 0.12, w: cw - 0.95, h: 0.4,
        fontSize: 14, bold: true, color: C.green,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      s.addText(f.desc, {
        x: cx + 0.15, y: cy + 0.65, w: cw - 0.3, h: 1.1,
        fontSize: 12, color: C.offWhite,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 6 — Live Demo Flow
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("How It Works", {
      x: 0.35, y: 0.22, w: 9.3, h: 0.65,
      fontSize: 36, bold: true, color: C.white,
      fontFace: "Arial Black", align: "left", valign: "top", margin: 0,
    });

    const steps = [
      {
        num: "1",
        action: "User sends message",
        detail: '"@jbot review the auth module"',
        color: C.panel,
      },
      {
        num: "2",
        action: "Manager analyzes & routes",
        detail: "Spawns a dedicated Worker session for this task",
        color: C.panelDark,
      },
      {
        num: "3",
        action: "Worker executes",
        detail: "Full Claude Code runs with file access and tools",
        color: "005599",
      },
      {
        num: "4",
        action: "Heartbeat updates",
        detail: "Progress messages appear every 60 seconds in chat",
        color: "006622",
      },
      {
        num: "5",
        action: "Results delivered",
        detail: "Final findings formatted as a Teams message with code blocks",
        color: C.greenDim,
      },
    ];

    steps.forEach((step, i) => {
      const sy = 1.1 + i * 0.88;
      const sh = 0.76;

      // Step number circle
      s.addShape(pres.shapes.OVAL, {
        x: 0.35, y: sy, w: 0.55, h: 0.55,
        fill: { color: step.color }, line: { color: step.color },
      });

      s.addText(step.num, {
        x: 0.35, y: sy, w: 0.55, h: 0.55,
        fontSize: 15, bold: true, color: C.white,
        fontFace: "Arial Black", align: "center", valign: "middle", margin: 0,
      });

      // Step row card
      s.addShape(pres.shapes.RECTANGLE, {
        x: 1.05, y: sy, w: 8.7, h: sh,
        fill: { color: C.cardBg }, line: { color: step.color },
      });

      // Left accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: 1.05, y: sy, w: 0.07, h: sh,
        fill: { color: step.color }, line: { color: step.color },
      });

      s.addText(step.action, {
        x: 1.25, y: sy + 0.05, w: 3.5, h: 0.32,
        fontSize: 14, bold: true, color: C.white,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      s.addText(step.detail, {
        x: 1.25, y: sy + 0.38, w: 8.3, h: 0.32,
        fontSize: 12, color: C.muted,
        fontFace: "Calibri", italic: true, align: "left", valign: "top", margin: 0,
      });

      // Connector arrow between steps
      if (i < steps.length - 1) {
        s.addShape(pres.shapes.LINE, {
          x: 0.62, y: sy + 0.55, w: 0, h: 0.26,
          line: { color: C.muted, width: 1 },
        });
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 7 — Use Cases
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Top header strip
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 1.05,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("What Can J-Bot Do?", {
      x: 0.4, y: 0, w: 9.2, h: 1.05,
      fontSize: 36, bold: true, color: C.bg,
      fontFace: "Arial Black", align: "left", valign: "middle", margin: 0,
    });

    // Left column: Code Analysis
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 1.2, w: 4.4, h: 4.1,
      fill: { color: C.cardBg }, line: { color: C.panel },
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 1.2, w: 4.4, h: 0.48,
      fill: { color: C.panel }, line: { color: C.panel },
    });

    s.addText("Code Analysis", {
      x: 0.3, y: 1.2, w: 4.4, h: 0.48,
      fontSize: 16, bold: true, color: C.green,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    const codeAnalysis = [
      { icon: "🐛", text: "Bug detection & root cause analysis" },
      { icon: "🔒", text: "Security review & vulnerability scanning" },
      { icon: "🏗️", text: "Architecture exploration & dependency maps" },
      { icon: "📊", text: "Code complexity & quality reports" },
      { icon: "🔍", text: "Cross-repo pattern search" },
    ];

    codeAnalysis.forEach((item, i) => {
      const iy = 1.82 + i * 0.68;

      s.addText(item.icon, {
        x: 0.45, y: iy, w: 0.45, h: 0.5,
        fontSize: 16, align: "center", valign: "middle", margin: 0,
      });

      s.addText(item.text, {
        x: 0.98, y: iy + 0.04, w: 3.5, h: 0.45,
        fontSize: 13, color: C.offWhite,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });

    // Right column: Automation
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.3, y: 1.2, w: 4.4, h: 4.1,
      fill: { color: C.cardBg }, line: { color: C.panelDark },
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.3, y: 1.2, w: 4.4, h: 0.48,
      fill: { color: "005599" }, line: { color: "005599" },
    });

    s.addText("Automation", {
      x: 5.3, y: 1.2, w: 4.4, h: 0.48,
      fontSize: 16, bold: true, color: C.white,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    const automation = [
      { icon: "🧪", text: "Automated test generation" },
      { icon: "📝", text: "Documentation writing & updates" },
      { icon: "🔧", text: "CI/CD pipeline debugging" },
      { icon: "📦", text: "Dependency upgrade guidance" },
      { icon: "🌐", text: "Multi-repo coordination tasks" },
    ];

    automation.forEach((item, i) => {
      const iy = 1.82 + i * 0.68;

      s.addText(item.icon, {
        x: 5.45, y: iy, w: 0.45, h: 0.5,
        fontSize: 16, align: "center", valign: "middle", margin: 0,
      });

      s.addText(item.text, {
        x: 5.98, y: iy + 0.04, w: 3.5, h: 0.45,
        fontSize: 13, color: C.offWhite,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 8 — Quick Setup
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("Get Started in 3 Steps", {
      x: 0.35, y: 0.22, w: 9.3, h: 0.65,
      fontSize: 36, bold: true, color: C.white,
      fontFace: "Arial Black", align: "left", valign: "top", margin: 0,
    });

    s.addText("Up and running in minutes", {
      x: 0.35, y: 0.85, w: 9.3, h: 0.35,
      fontSize: 14, color: C.green,
      fontFace: "Calibri", italic: true, align: "left", valign: "top", margin: 0,
    });

    const steps = [
      {
        num: "01",
        title: "Configure",
        subtitle: "Edit  ~/.jbot/config.yaml",
        lines: [
          "Set your Teams chat IDs (group & DM)",
          "Configure max_workers (default: 5)",
          "Point to your project working directories",
        ],
        code: "chat_ids:\n  - your-group-chat-id\nmax_workers: 5",
      },
      {
        num: "02",
        title: "Authenticate",
        subtitle: "Login to Teams & Claude CLIs",
        lines: [
          "Run  teams-cli auth login  to connect Teams",
          "Run  claude  and complete the auth flow",
          "Verify with  jbot --check",
        ],
        code: "teams-cli auth login\nclaude\njbot --check",
      },
      {
        num: "03",
        title: "Launch",
        subtitle: "Start the daemon and chat",
        lines: [
          "Run  jbot --daemon  to start in background",
          "Open any Teams chat and type  @jbot hello",
          "J-Bot will respond and confirm it's ready",
        ],
        code: "jbot --daemon\n# Then in Teams:\n@jbot hello",
      },
    ];

    steps.forEach((step, i) => {
      const sy = 1.35 + i * 1.38;
      const sh = 1.22;

      // Big number
      s.addText(step.num, {
        x: 0.35, y: sy, w: 0.75, h: sh,
        fontSize: 36, bold: true, color: C.green,
        fontFace: "Arial Black", align: "center", valign: "middle", margin: 0,
      });

      // Card
      s.addShape(pres.shapes.RECTANGLE, {
        x: 1.15, y: sy, w: 8.55, h: sh,
        fill: { color: C.cardBg }, line: { color: C.panelDark },
      });

      // Title + subtitle
      s.addText(step.title, {
        x: 1.3, y: sy + 0.07, w: 2.5, h: 0.4,
        fontSize: 17, bold: true, color: C.white,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      s.addText(step.subtitle, {
        x: 1.3, y: sy + 0.47, w: 3.5, h: 0.3,
        fontSize: 12, color: C.green,
        fontFace: "Calibri", italic: true, align: "left", valign: "top", margin: 0,
      });

      // Bullet points
      s.addText(step.lines.map((l, li) => ({
        text: l,
        options: { bullet: true, breakLine: li < step.lines.length - 1, fontSize: 11, color: C.offWhite },
      })), {
        x: 1.3, y: sy + 0.77, w: 3.8, h: 0.4,
        fontFace: "Calibri",
      });

      // Code block
      s.addShape(pres.shapes.RECTANGLE, {
        x: 5.2, y: sy + 0.08, w: 4.3, h: sh - 0.16,
        fill: { color: "0d1117" }, line: { color: C.green },
      });

      s.addText(step.code, {
        x: 5.35, y: sy + 0.1, w: 4.0, h: sh - 0.2,
        fontSize: 11, color: C.green,
        fontFace: "Consolas", align: "left", valign: "middle", margin: 4,
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 9 — Roadmap & Contact
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Top header
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 1.05,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("Roadmap & Contact", {
      x: 0.4, y: 0, w: 9.2, h: 1.05,
      fontSize: 36, bold: true, color: C.bg,
      fontFace: "Arial Black", align: "left", valign: "middle", margin: 0,
    });

    // Roadmap section header
    s.addText("What's Coming Next", {
      x: 0.35, y: 1.2, w: 5.5, h: 0.4,
      fontSize: 16, bold: true, color: C.offWhite,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    const roadmap = [
      { icon: "🖥️", label: "Web Dashboard", detail: "Visual job queue and cost analytics" },
      { icon: "⏰", label: "Cron Scheduling", detail: "Run recurring tasks on a schedule" },
      { icon: "🏢", label: "Multi-team Support", detail: "Scale across multiple Teams tenants" },
      { icon: "🛒", label: "Skill Marketplace", detail: "Shareable domain-specific skill packs" },
    ];

    roadmap.forEach((item, i) => {
      const rx = 0.35 + (i % 2) * 2.8;
      const ry = 1.75 + Math.floor(i / 2) * 1.1;
      const rw = 2.55;
      const rh = 0.95;

      s.addShape(pres.shapes.RECTANGLE, {
        x: rx, y: ry, w: rw, h: rh,
        fill: { color: C.cardBg }, line: { color: C.panelDark },
      });

      s.addText(item.icon, {
        x: rx + 0.1, y: ry + 0.05, w: 0.5, h: 0.5,
        fontSize: 18, align: "center", valign: "middle", margin: 0,
      });

      s.addText(item.label, {
        x: rx + 0.65, y: ry + 0.08, w: rw - 0.75, h: 0.35,
        fontSize: 13, bold: true, color: C.green,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      s.addText(item.detail, {
        x: rx + 0.65, y: ry + 0.48, w: rw - 0.75, h: 0.4,
        fontSize: 11, color: C.muted,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });

    // Vertical divider
    s.addShape(pres.shapes.LINE, {
      x: 6.0, y: 1.15, w: 0, h: 4.2,
      line: { color: C.panelDark, width: 1 },
    });

    // Contact section
    s.addText("Get in Touch", {
      x: 6.3, y: 1.2, w: 3.5, h: 0.4,
      fontSize: 16, bold: true, color: C.offWhite,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    // Contact card
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.3, y: 1.75, w: 3.45, h: 1.35,
      fill: { color: C.cardBg }, line: { color: C.green },
    });

    s.addShape(pres.shapes.OVAL, {
      x: 6.45, y: 1.9, w: 0.75, h: 0.75,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("JW", {
      x: 6.45, y: 1.9, w: 0.75, h: 0.75,
      fontSize: 17, bold: true, color: C.bg,
      fontFace: "Arial Black", align: "center", valign: "middle", margin: 0,
    });

    s.addText("Jackey Wang", {
      x: 7.3, y: 1.85, w: 2.3, h: 0.4,
      fontSize: 15, bold: true, color: C.white,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    s.addText("jackeyw@nvidia.com", {
      x: 7.3, y: 2.28, w: 2.3, h: 0.35,
      fontSize: 12, color: C.green,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    // Links section
    s.addText("Resources", {
      x: 6.3, y: 3.3, w: 3.45, h: 0.35,
      fontSize: 14, bold: true, color: C.offWhite,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    const links = [
      { icon: "📄", label: "Confluence Page", detail: "Full docs & API reference" },
      { icon: "💬", label: "Slack Channel", detail: "#jbot — questions & feedback" },
    ];

    links.forEach((link, i) => {
      const ly = 3.78 + i * 0.75;

      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.3, y: ly, w: 3.45, h: 0.62,
        fill: { color: C.cardBg }, line: { color: C.panelDark },
      });

      s.addText(link.icon, {
        x: 6.38, y: ly + 0.05, w: 0.4, h: 0.5,
        fontSize: 14, align: "center", valign: "middle", margin: 0,
      });

      s.addText(link.label, {
        x: 6.85, y: ly + 0.05, w: 2.8, h: 0.25,
        fontSize: 12, bold: true, color: C.green,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      s.addText(link.detail, {
        x: 6.85, y: ly + 0.32, w: 2.8, h: 0.25,
        fontSize: 11, color: C.muted,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });

    // Bottom closing line
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.3, w: 10, h: 0.325,
      fill: { color: C.green }, line: { color: C.green },
    });

    s.addText("NVIDIA Interconnect Shanghai  •  J-Bot v1.0  •  March 2026", {
      x: 0, y: 5.3, w: 10, h: 0.325,
      fontSize: 11, color: C.bg,
      fontFace: "Calibri", bold: true, align: "center", valign: "middle", margin: 0,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SLIDE 10 — Easter Egg: This Deck Was Built by J-Bot
  // ═══════════════════════════════════════════════════════════════════════════
  {
    const gold = "FFD700";
    const goldDim = "B8860B";

    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Top header band — gold instead of green to signal the special slide
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 1.05,
      fill: { color: gold }, line: { color: gold },
    });

    // "EASTER EGG" label badge on the left of the header
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 0.2, w: 1.4, h: 0.45,
      fill: { color: C.bg }, line: { color: C.bg },
    });
    s.addText("EASTER EGG", {
      x: 0.3, y: 0.2, w: 1.4, h: 0.45,
      fontSize: 9, bold: true, color: gold,
      fontFace: "Arial Black", align: "center", valign: "middle", margin: 2,
    });

    // Main header title
    s.addText("Meta Demo: This Deck Was Built by J-Bot", {
      x: 1.85, y: 0, w: 7.9, h: 1.05,
      fontSize: 24, bold: true, color: C.bg,
      fontFace: "Arial Black", align: "left", valign: "middle", margin: 0,
    });

    // ── Left side: Single Teams Message box ─────────────────────────────────
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 1.2, w: 3.0, h: 2.4,
      fill: { color: C.panel }, line: { color: gold },
    });

    // Gold top strip on the input box
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: 1.2, w: 3.0, h: 0.06,
      fill: { color: gold }, line: { color: gold },
    });

    s.addText("Single Teams Message", {
      x: 0.3, y: 1.28, w: 3.0, h: 0.42,
      fontSize: 12, bold: true, color: gold,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });

    // Teams chat bubble appearance
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: 1.82, w: 2.6, h: 1.55,
      fill: { color: C.cardBg }, line: { color: C.accent },
    });

    s.addText("💬", {
      x: 0.5, y: 1.82, w: 0.45, h: 0.45,
      fontSize: 16, align: "center", valign: "middle", margin: 0,
    });

    s.addText("@jbot", {
      x: 0.96, y: 1.87, w: 1.8, h: 0.3,
      fontSize: 11, bold: true, color: C.accent,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    s.addText("Create a launch email, PPT, Confluence page, and demo video for J-Bot", {
      x: 0.56, y: 2.2, w: 2.4, h: 1.05,
      fontSize: 11, color: C.offWhite,
      fontFace: "Calibri", align: "left", valign: "top", margin: 0,
    });

    // ── Arrow pointing right ─────────────────────────────────────────────────
    s.addShape(pres.shapes.RIGHT_ARROW, {
      x: 3.45, y: 2.1, w: 0.6, h: 0.5,
      fill: { color: gold }, line: { color: gold },
    });

    // ── Right side: 2x2 grid of output cards ────────────────────────────────
    const outputs = [
      {
        icon: "📧",
        label: "Email Draft",
        detail: "Professional HTML email in Outlook Drafts",
        accentColor: C.green,
      },
      {
        icon: "📊",
        label: "PowerPoint",
        detail: "9-slide deck with architecture diagrams",
        accentColor: C.green,
      },
      {
        icon: "📄",
        label: "Confluence",
        detail: "Full technical docs under AI Initiatives",
        accentColor: C.accent,
      },
      {
        icon: "🎬",
        label: "Demo Video",
        detail: "90s Remotion video with Teams UI simulation",
        accentColor: C.accent,
      },
    ];

    const cardCols = [4.2, 7.0];
    const cardRows = [1.2, 2.65];
    const cardW = 2.65;
    const cardH = 1.25;

    outputs.forEach((out, i) => {
      const cx = cardCols[i % 2];
      const cy = cardRows[Math.floor(i / 2)];

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cardW, h: cardH,
        fill: { color: C.cardBg }, line: { color: out.accentColor },
        shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.25 },
      });

      // Top accent strip
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cardW, h: 0.055,
        fill: { color: out.accentColor }, line: { color: out.accentColor },
      });

      // Icon
      s.addText(out.icon, {
        x: cx + 0.1, y: cy + 0.1, w: 0.5, h: 0.5,
        fontSize: 20, align: "center", valign: "middle", margin: 0,
      });

      // Label
      s.addText(out.label, {
        x: cx + 0.68, y: cy + 0.1, w: cardW - 0.82, h: 0.38,
        fontSize: 13, bold: true, color: C.white,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });

      // Detail text
      s.addText(out.detail, {
        x: cx + 0.1, y: cy + 0.58, w: cardW - 0.2, h: 0.58,
        fontSize: 11, color: C.offWhite,
        fontFace: "Calibri", align: "left", valign: "top", margin: 0,
      });
    });

    // ── Bottom stats bar ─────────────────────────────────────────────────────
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 4.35, w: 10, h: 0.9,
      fill: { color: C.panelDark }, line: { color: gold },
    });

    // Gold left accent on stats bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 4.35, w: 0.06, h: 0.9,
      fill: { color: gold }, line: { color: gold },
    });

    const stats = [
      "4 parallel workers",
      "5 enterprise systems",
      "~10 minutes",
      "Zero terminal switching",
    ];

    stats.forEach((stat, i) => {
      const sx = 0.3 + i * 2.42;

      // Separator pipe (except before first)
      if (i > 0) {
        s.addShape(pres.shapes.LINE, {
          x: sx - 0.15, y: 4.45, w: 0, h: 0.7,
          line: { color: goldDim, width: 1 },
        });
      }

      s.addText(stat, {
        x: sx, y: 4.35, w: 2.3, h: 0.9,
        fontSize: 13, bold: true, color: gold,
        fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
      });
    });

    // ── Tiny egg emoji decoration (bottom-right corner) ──────────────────────
    s.addText("🥚", {
      x: 9.35, y: 4.42, w: 0.55, h: 0.55,
      fontSize: 20, align: "center", valign: "middle", margin: 0,
    });
  }

  // Save
  const outPath = "/Users/jackeyw/Downloads/claude_demo/cyber_teams_niuma/niuma-bot-intro.pptx";
  await pres.writeFile({ fileName: outPath });
  console.log("Saved:", outPath);
}

buildPresentation().catch(err => {
  console.error(err);
  process.exit(1);
});
