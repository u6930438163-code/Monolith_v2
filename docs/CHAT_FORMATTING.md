# Chat formatting requirements

LibreChat main chat must support safe Markdown, KaTeX math, scientific notation with superscripts, syntax-highlighted copyable code, horizontally scrollable tables, expandable long replies, per-agent cards (Aria, Alex, Astyria, Aurelius), thumbs reactions, and tool-result cards for budget, missions, diagnostics, spacecraft and facilities.

Mobile: responsive fonts, no horizontal viewport overflow, long URL wrapping, code scrolling, accessible touch targets, readable Polish characters.

Security: sanitize generated HTML; never execute model-produced code automatically; confirm purchases and destructive actions.

Acceptance: test negative exponents, wide tables, long logs, long code blocks, Android narrow screens, and streaming messages.

Status: specification only; implementation pending.
