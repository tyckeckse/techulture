# 🧭 Techulture

A small, self-updating digest of Swedish culture and news, built from public feeds and picked partly by a local language model that runs inside GitHub Actions.

**Live page:** https://techulture.vercel.app · **Presentation with diagrams:** [presentation/index.html](presentation/index.html)

## What it does

Techulture gathers Swedish culture news in one quiet place: culture desks, art criticism and university press rooms, plus a short column of general news.


## How the page is made

Once an hour, a job on GitHub fetches the latest items from eleven sources, drops what is too old, lets the AI pick the news and writes one simple web page. That page is then published on Vercel. There is no database and no server: each hour the page is built again from scratch.

![Eleven sources are fetched every hour, filtered, the news is picked by a small AI, and one page is published](presentation/how-it-works.svg)

If a source is down, it is simply skipped for that hour. And if most sources fail at once, the old page stays up rather than being replaced by an empty one.

## A small AI that picks the news

SVT and SR Ekot publish dozens of headlines a day. The AI gets the fresh ones, about ten at a time, and gives each a score from 0 to 20: low for routine updates, sport and celebrity, high for important or surprising news that many people will want to understand. 

![Headlines get scores from the AI and only the highest scored are shown](presentation/picking-the-news.svg)

The AI is Qwen2.5 3B, a small open model from Hugging Face. 

## Sources

**Culture:** SVT Kultur, SR Kulturnytt, Expressen Kultur, Kunstkritikk, Konstfack, and the universities in Stockholm, Uppsala, Lund and Södertörn.
**News:** SVT Nyheter and SR Ekot, picked by the AI.

---

*The majority of text in this README was AI-generated.*
