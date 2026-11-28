# Relevance order of the estimation samples

Order of the samples by how useful they are as examples in the estimator's context. This order is a judgment, not data. It assumes a general web and software agency as the client mix. See "When to reorder" at the end.

## How the order was decided

Each sample was ranked on three criteria:

1. **How common the project type is.** The more often such a request arrives, the more often the example helps.
2. **How much new sizing information it gives the model.** Effort that is driven by different factors (sources, experimentation, hardware, legacy rules) teaches more than one more variation of a web app.
3. **How costly a bad estimate would be.** Types where hidden work is easy to miss rank higher.

## Ranking

| # | Sample | Type | Stack | Hours |
|---|--------|------|-------|-------|
| 1 | Inventory and purchasing platform | Web B2B, ERP integration, data migration | React, NestJS, PostgreSQL, AWS | 1,348 |
| 2 | Ingenia knowledge assistant | AI / LLM (RAG) | Python, FastAPI, Bedrock, OpenSearch | 900 |
| 3 | RutaFix field-service SaaS | Multi-tenant SaaS, billing, compliance | Ruby on Rails, Hotwire, Heroku | 2,055 |
| 4 | Studio Ritmo booking app | Mobile consumer app | Flutter, Firebase, Vue | 1,102 |
| 5 | Mercado Verde analytics platform | Data and analytics | Azure, Databricks, dbt, Power BI | 1,405 |
| 6 | Seguros Andina modernization | Legacy modernization | .NET 8, Angular, SQL Server | 2,408 |
| 7 | Clínica Sonríe website | Small marketing site | Astro, Storyblok, Netlify | 110 |
| 8 | LácteosSur plant monitoring station | Desktop + IoT | .NET WPF, Go, MQTT, AWS IoT | 1,800 |

## Why each one sits where it does

1. **Inventory and purchasing platform.** A B2B web platform with an ERP integration and a data migration is the typical project of a software agency. It is the baseline that the other samples differ from, so it goes first.
2. **Ingenia knowledge assistant.** AI features are among the most requested projects now, and they are hard to size. The estimator needs to see time-boxed experimentation, evals, guardrails and a higher contingency. It is also the domain this estimator lives in.
3. **RutaFix field-service SaaS.** Many clients want a product instead of an internal tool. It covers tenancy, subscription billing and SOC 2 work, which are the items most often forgotten. Mistakes here are expensive, so it ranks high.
4. **Studio Ritmo booking app.** Mobile apps are very common and have their own work that web samples do not show: store releases and reviews, payments with strong customer authentication, push notifications and device testing. Their effort is more predictable than the AI or SaaS cases, so they rank a bit lower.
5. **Mercado Verde analytics platform.** Data projects are frequent. Their effort follows the number of sources and the data quality, not the number of screens, which is a different sizing logic. They are somewhat less common for a general agency.
6. **Seguros Andina modernization.** It teaches an important and different profile: no new features, reverse-engineering, characterization tests, parallel runs and high contingency. It ranks lower because these projects are less frequent, and their size varies a lot from case to case.
7. **Clínica Sonríe website.** Small sites are very common, but a model can size simple work with little help. Its main value is calibrating the low end, so that small requests do not get inflated with phases and overhead they do not need.
8. **LácteosSur plant monitoring station.** It is the most specialized case, with hardware protocols, offline-first sync and two release pipelines. It is the rarest in a typical client mix, but it is the only sample that covers desktop and IoT. Being last means it is the least likely to be needed, not that it is unimportant.

## When to reorder

- If most real clients are **small businesses**, move the website (7) near the top.
- If the clients are **industrial or manufacturing** companies, move the plant monitoring station (8) and the analytics platform (5) up.
- If the pipeline has many **enterprise modernization** requests, move Seguros Andina (6) up.
- With real data, such as the project types of the last 20 to 30 requests, replace this judgment with frequency.
- The order also matters for the prompt itself. When examples are added to a prompt, the most relevant ones should come first, and if the prompt size has to be cut, the last ones are dropped first.
