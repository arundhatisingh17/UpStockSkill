---
name: equity-research
description: Part of the trading skill. Produces a sourced fundamental research report on a stock (financials, peers, catalysts, valuation scenarios, risks, technical context, insider activity). Use when she asks to research, analyze, or "what do you think of" a ticker, or wants fundamentals to pair with the trend-identification signal.
---

# Equity research (fundamentals)

Framework adapted from quant-sentiment-ai/claude-equity-research (MIT licence; reviewed, it is a prompt-only plugin using WebSearch/WebFetch, no scripts). Use for research only; never place orders.

## Method
Run web searches in parallel for: (1) recent earnings, revenue growth, margins, KPIs, analyst coverage; (2) peers, sector performance, competitive position; (3) technicals, options flow, insider activity, institutional ownership, regulatory issues. Prefer primary sources (SEC filings, earnings releases, company IR) over blogs.

## Sourcing rules (important)
- Every number gets a date and a source. If it cannot be found, write "not found"; never estimate or invent figures, price targets, analyst names, insider trades, or options-flow data.
- Mark data as delayed/unverified where applicable. Quote analyst targets only if a source shows them.

## Report sections
1. **Summary**: thesis in 2 lines, key catalyst, key risk. Describe what the evidence supports (constructive / neutral / cautious) rather than telling her to buy or sell.
2. **Fundamentals**: revenue growth, margins, EPS, balance sheet, with periods (YoY/QoQ).
3. **Peers**: P/E, P/S, EV/EBITDA vs named competitors.
4. **Catalysts**: near-term (0-6m, with dates), medium-term, event-driven.
5. **Valuation scenarios**: bull/base/bear with assumptions and rough probabilities; show the arithmetic.
6. **Risks**: company-specific and macro; what would make the thesis wrong.
7. **Technical context**: price vs 52-week range, support/resistance, volume. Hand off to `trend-identification` for the trend and entry/exit signals.
8. **Insiders / ownership**: with dollar amounts and dates, if sourced.
9. **Sizing context**: volatility/beta and a cap such as 2-5% of the portfolio per position (general risk practice, not a personal recommendation).

## How it combines with trend-identification
Use both, in this order: fundamentals decide whether a stock is worth watching; the Dow Theory trend decides when to enter (higher low then higher high, stop at the higher low) and when to exit (lower high then lower low). A BUY needs both: an acceptable fundamental picture and a trend signal. A SELL on a trend break applies even if fundamentals look fine. Log simulated trades in the paper ledger with `Signal source` = `equity-research + trend`.

## Always include
"Educational research, not investment advice. I'm not a licensed advisor. Verify figures with primary sources. All investing risks loss."
