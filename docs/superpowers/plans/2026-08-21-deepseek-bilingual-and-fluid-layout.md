# DeepSeek Bilingual CMS and Fluid Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement task-by-task.

**Goal:** Add safe asynchronous English-draft generation with DeepSeek-V4-Flash and make public/admin pages fluidly adapt across reasonable screen widths.

**Architecture:** Store a frozen Chinese revision, translation task, translation result and language-specific published revision separately. A single worker process, launched from the same Docker image and backed by PostgreSQL, claims one task at a time; no Redis or external queue is used. CSS relies on intrinsic layouts and text-safe component rules rather than device pages.

**Tech Stack:** Next.js, TypeScript, Prisma/PostgreSQL, structured rich-text JSON, DeepSeek Chat Completions JSON Output, Tailwind CSS, Vitest and Playwright.

**Spec:** `docs/superpowers/specs/2026-08-19-rongelec-fullstack-website-design.md`

## Global Constraints

- `DEEPSEEK_API_KEY` is server-only and never enters the browser, logs, build output or Git.
- Use `deepseek-v4-flash`, International Maritime English and British spelling.
- The first publication requires confirmed Chinese and English; published English stays online while later Chinese edits make it stale.
- One translation worker and one in-flight source revision per content item; no Redis, RabbitMQ or WebSocket.
- No document-level horizontal overflow from 320px to 2560px, including English text expansion and 200% zoom.

---

### Task 1: Persist revisions, glossary and queue state

**Files:**
- Modify: `prisma/schema.prisma`
- Create: `src/lib/translation/state.ts`
- Test: `src/lib/translation/state.test.ts`

- [ ] Write failing tests for `QUEUED`, `PROCESSING`, `AI_DRAFT`, `FAILED`, `CONFIRMED` and `STALE` transitions.
- [ ] Add `TranslationTask`, `TranslationGlossary`, source revision snapshot ID, chunk totals, attempts, locked time, provider/model/prompt/glossary metadata and a partial unique index on `(content_type, content_id, source_revision)` for queued/processing tasks.
- [ ] Run `npx prisma migrate dev --name add_translation_tasks` and `npm test -- src/lib/translation/state.test.ts`.
- [ ] Commit with `git commit -m "feat: persist translation task state"`.

### Task 2: Build block-aware DeepSeek adapter

**Files:**
- Create: `src/lib/translation/rich-text-blocks.ts`
- Create: `src/lib/translation/deepseek.ts`
- Create: `src/lib/translation/maritime-prompt.ts`
- Test: `src/lib/translation/deepseek.test.ts`

- [ ] Test that paragraph blocks retain inline mark placeholders, paths and non-text structure after translation; code blocks, numbers, IMO identifiers and dates must be skipped.
- [ ] Extract frozen rich-text JSON by array path, translate paragraph-sized blocks, inject only matching path results, and reject missing/extra paths or placeholder tokens.
- [ ] Match at most 50 active glossary records present in the source text; validate expected English glossary terms in the returned translation.
- [ ] Send JSON Output to `https://api.deepseek.com/chat/completions` with `deepseek-v4-flash`, bounded chunks and a prompt demanding International Maritime English, British spelling and exact path preservation.
- [ ] Retry an empty response, HTTP 429, 500 or 503 once per chunk; preserve the old English version on final failure.
- [ ] Run `npm test -- src/lib/translation/deepseek.test.ts` and commit with `git commit -m "feat: translate rich text with DeepSeek"`.

### Task 3: Run durable PostgreSQL-backed translation jobs

**Files:**
- Create: `src/workers/translation-worker.ts`
- Create: `src/lib/translation/tasks.ts`
- Create: `src/app/api/admin/translation-tasks/[id]/route.ts`
- Test: `src/workers/translation-worker.test.ts`

- [ ] Test concurrent claims, duplicate source-version enqueue prevention, failed-task retry and 10-minute processing-timeout recovery.
- [ ] Claim work in a short transaction using `FOR UPDATE SKIP LOCKED`, commit before calling DeepSeek, then open a new short transaction to update progress/result.
- [ ] Start the same image with a separate `worker` command, limit translation concurrency to one and set a small memory limit; it is not an external queue service.
- [ ] Return only task ID, status, attempts, `doneChunks`, `totalChunks` and retry capability from the authenticated polling endpoint.
- [ ] Run `npm test -- src/workers/translation-worker.test.ts` and commit with `git commit -m "feat: process translation jobs asynchronously"`.

### Task 4: Add bilingual editor and publication behavior

**Files:**
- Modify: `src/app/admin/content/[id]/editor.tsx`
- Create: `src/app/api/admin/content/[id]/translations/en/route.ts`
- Modify: `src/lib/content/publication.ts`
- Test: `src/app/api/admin/content/[id]/translations/en/route.test.ts`

- [ ] Add Chinese-tab actions: save, generate English draft and create blank English; add English-tab state badge, polling progress, manual edit, preview and confirmation.
- [ ] Freeze Chinese revision before enqueueing; regeneration creates a new English draft and revision rather than overwriting a published or manually edited English version.
- [ ] Use last confirmed English revision for public `/en` pages while English is stale; missing English returns 404 and disables the language switch as a button, not a link.
- [ ] Run route/component tests and commit with `git commit -m "feat: add bilingual translation workflow"`.

### Task 5: Make layouts fluid and test multilingual SEO

**Files:**
- Modify: `src/app/globals.css`
- Modify: `src/components/layout/*`
- Modify: `src/components/editor/*`
- Modify: `src/app/[locale]/**/page.tsx`
- Test: `e2e/fluid-layout.spec.ts`
- Test: `e2e/hreflang.spec.ts`

- [ ] Use `clamp()`, `minmax()`, `auto-fit`, flex wrapping, `min-inline-size: 0`, `overflow-wrap: anywhere`, `text-wrap: balance`, `aspect-ratio` and responsive media constraints.
- [ ] Apply `lang` to each public document, `hyphens: auto` to English prose, `translate="no"` to ship names/model identifiers and local `lang="en"` component adjustments without shrinking body copy below readability.
- [ ] Emit reciprocal canonical/hreflang pairs plus `x-default` only for published counterparts; include only published localized URLs in the Sitemap and use locale-specific `lastmod`.
- [ ] Sweep 320, 360, 390, 412, 480, 600, 768, 820, 960, 1024, 1280, 1440, 1920 and 2560px, including English navigation and 200% zoom.
- [ ] Run `npm test && npx playwright test && npm run build`, then commit with `git commit -m "test: cover fluid bilingual publishing"`.
