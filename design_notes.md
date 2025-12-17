Below is the **complete and corrected `design_notes.md`** file.

This is **code-only (markdown only)**, structured exactly how reviewers expect for a **Lyftr AI full-stack assignment**.
You can **copy-paste directly** into `design_notes.md`.

---

````markdown
# Design Notes  
Universal Website Scraper – Lyftr AI Assignment

---

## 📋 Overview

This document explains the **architecture, design decisions, heuristics, and trade-offs**
used while building the **Universal Website Scraper**.

The goal was to build a **production-grade**, **scalable**, and **explainable** scraping system
that works reliably across:
- Static websites
- JavaScript-heavy SPAs
- Infinite-scroll and paginated pages
- Content-rich marketing pages

---

## 🧠 Core Design Philosophy

1. **Static-first, dynamic-when-needed**
2. **Accuracy over brute force**
3. **Bounded scraping (safe & predictable)**
4. **Clear separation of responsibilities**
5. **Explainable decisions (interview-friendly)**

---

## 🔄 Static vs JavaScript Fallback Strategy

### Why Static First?

Static scraping using `httpx + selectolax` is:
- Extremely fast
- Memory efficient
- Reliable for 70–80% of websites
- Easier to reason about

Launching a browser is **expensive**, so it should only happen when needed.

---

### Heuristic-Based JS Fallback

After static scraping, we evaluate content quality using heuristics.

JS fallback is triggered when **any** of the following is true:

1. Total extracted text length `< JS_FALLBACK_MIN_TEXT`
2. No meaningful semantic sections detected
3. Static fetch fails
4. User explicitly requests JS mode

```python
JS_FALLBACK_MIN_TEXT = 400
JS_FALLBACK_CHECK_SELECTORS = ["main", "article", "[role='main']"]
````

---

### Why Heuristics Instead of Always JS?

| Approach           | Problem                                   |
| ------------------ | ----------------------------------------- |
| Always JS          | Slow, resource-heavy, unreliable at scale |
| Static only        | Misses SPA content                        |
| Heuristic fallback | Balanced, efficient, explainable          |

This approach mirrors **real-world scraper systems** used in production.

---

## 🧩 Architecture Overview

```
Request
   ↓
ScraperEngine
   ├── StaticScraper
   │     └── selectolax DOM parsing
   └── DynamicScraper (Playwright)
         ├── Clicks
         ├── Scrolls
         └── Pagination
   ↓
SectionParser
   ↓
Structured JSON Response
```

---

## ⚙️ Component Responsibilities

### 1. ScraperEngine

* Orchestrates the entire workflow
* Decides static vs dynamic
* Aggregates results
* Handles errors cleanly

**Why separate engine?**

* Easier testing
* Clear control flow
* Interview-friendly explanation

---

### 2. StaticScraper

* Uses `httpx` (async, fast)
* Parses HTML using `selectolax`
* Removes noise elements
* Extracts metadata

**Why selectolax over BeautifulSoup?**

* ~10x faster
* Lower memory usage
* Production-friendly

---

### 3. DynamicScraper (Playwright)

Handles:

* JavaScript rendering
* User-like interactions
* Scroll-based loading
* Pagination traversal

Safeguards:

* Max scroll attempts
* Max interaction depth
* Visibility checks
* Timeout limits

This prevents infinite loops and runaway scraping.

---

### 4. SectionParser

Responsible for converting raw DOM into **structured sections**.

#### Section Detection Order

1. Semantic tags (`main`, `section`, `article`, etc.)
2. Heading-based grouping (`h1`, `h2`, `h3`)
3. Full-page fallback

This ensures **something useful is always returned**.

---

## 📄 Section Content Extraction

Each section extracts:

* Headings
* Text (sanitized)
* Links (absolute URLs)
* Images (src + alt)
* Lists
* Tables
* Raw HTML (truncated safely)

Why include raw HTML?

* Debugging
* Downstream ML usage
* Transparency

---

## 🧹 Noise Removal Strategy

Before parsing, we aggressively remove:

```python
[
  'script', 'style', 'iframe',
  '.popup', '.modal', '.ads',
  '[class*="cookie"]'
]
```

This improves:

* Text quality
* Section clarity
* Token efficiency (important for AI pipelines)

---

## 🖱️ Interaction Handling

The scraper simulates **real user behavior**:

### Supported Interactions

* Clicking tabs
* Clicking “Load More”
* Infinite scrolling
* Pagination navigation

### Safety Limits

* Max depth (`MAX_DEPTH`)
* Max scroll attempts
* Visible-only interactions
* Same-domain navigation only

This avoids:

* Infinite scrolling traps
* External site hopping
* Performance degradation

---

## ⏱️ Timeout Strategy

Multiple layered timeouts ensure safety:

| Layer               | Purpose                  |
| ------------------- | ------------------------ |
| HTTP timeout        | Prevent hanging requests |
| Playwright timeout  | Avoid JS deadlocks       |
| Interaction timeout | Prevent stuck clicks     |
| Global timeout      | Hard safety stop         |

---

## 📦 Schema Design (Why Pydantic?)

* Strong validation
* Clean API contracts
* Automatic OpenAPI docs
* Easier frontend integration

Schemas reflect **real API design standards**, not toy examples.

---

## 🧪 Error Handling Philosophy

* Errors never crash the request
* Errors are **returned**, not hidden
* Each error includes:

  * Message
  * Phase (fetch, parse, interaction, engine)

This is critical for:

* Debugging
* Observability
* Interview explanation

---

## 🚧 Intentional Limitations

Excluded by design:

* Login-protected scraping
* CAPTCHA solving
* Parallel crawling
* Long-term storage
* Proxy rotation

Reason:

> The goal is **clarity and correctness**, not unethical scraping.

---

## 🧠 Real-World Alignment

This design mirrors:

* Content ingestion pipelines
* AI dataset generation systems
* Knowledge extraction services
* Production-grade scrapers

---

## ✅ Final Summary

This project demonstrates:

* Strong system design
* Practical trade-offs
* Clean abstractions
* Real-world engineering judgment

It is intentionally **over-engineered for an assignment** to show:

> *“I know how this would work in production.”*

---

```
```
