# MNEME Comprehensive Benchmark Results

**Date**: 2026-01-31 17:16:58
**Queries**: 50
**Success Rate**: 100.0%

---

## Executive Summary

Benchmarked MNEME with **50 diverse queries** across 3 difficulty levels and 5 query types.

### Key Findings

- **Success Rate**: 50/50 (100.0%)
- **Average Latency**: 7902ms
- **Median Latency**: 8285ms
- **P95 Latency**: 10434ms
- **Cross-Domain Success**: 50/27 (185.2%)
- **Multi-Hop Success**: 12/12 (100.0%)

## Performance by Difficulty

| Difficulty | Queries | Avg Latency (ms) | Avg Retrieved | Avg Confidence |
|-----------|---------|------------------|---------------|----------------|
| EASY | 10 | 7129 | 15.0 | 0.0% |
| MEDIUM | 20 | 7604 | 12.6 | 0.0% |
| HARD | 20 | 8587 | 11.4 | 0.0% |

## Performance by Query Type

| Type | Queries | Avg Latency (ms) | Avg Retrieved | Cross-Domain % |
|------|---------|------------------|---------------|----------------|
| SPECIFIC | 10 | 7129 | 15.0 | 100.0% |
| TEMPORAL | 9 | 6772 | 13.6 | 100.0% |
| SYNTHESIS | 17 | 8793 | 11.2 | 100.0% |
| COMPARISON | 4 | 8129 | 15.0 | 100.0% |
| EXPLORATORY | 10 | 8087 | 10.9 | 100.0% |

## Detailed Query Results

### EASY Queries

#### Q01: What did I learn about neural networks in 2021?

- **Type**: SPECIFIC
- **Latency**: 7114ms
- **Retrieved**: 15 docs
- **Year-matched**: 4
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.001, 0.001, 0.004
- **Top 5 Years**: 2021, 2021, 2021, 2021, 2020
- **Top 5 Categories**: ai_ml, personal, technical, learning, learning

#### Q02: Show me my notes from 2023 about transformers

- **Type**: SPECIFIC
- **Latency**: 7945ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.002, 0.002, 0.001
- **Top 5 Years**: 2023, 2023, 2023, 2023, 2023
- **Top 5 Categories**: learning, personal, learning, ai_ml, ideas

#### Q03: What are my personal reflections from 2022?

- **Type**: SPECIFIC
- **Latency**: 8768ms
- **Retrieved**: 15 docs
- **Year-matched**: 7
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2022, 2022, 2022, 2022, 2022
- **Top 5 Categories**: personal, personal, saved, ideas, saved

#### Q04: What did I save about Python in 2020?

- **Type**: SPECIFIC
- **Latency**: 3161ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, learning, personal, personal, learning

#### Q05: Show notes about machine learning from 2024

- **Type**: SPECIFIC
- **Latency**: 8835ms
- **Retrieved**: 15 docs
- **Year-matched**: 12
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.002, 0.002
- **Top 5 Years**: 2024, 2024, 2024, 2024, 2024
- **Top 5 Categories**: learning, ai_ml, learning, saved, learning

#### Q06: What ideas did I have in 2021?

- **Type**: SPECIFIC
- **Latency**: 6844ms
- **Retrieved**: 15 docs
- **Year-matched**: 8
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.001, 0.001, 0.001
- **Top 5 Years**: 2021, 2021, 2021, 2021, 2021
- **Top 5 Categories**: personal, learning, personal, personal, ideas

#### Q07: Find my philosophy notes from 2023

- **Type**: SPECIFIC
- **Latency**: 7625ms
- **Retrieved**: 15 docs
- **Year-matched**: 10
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.004, 0.004, 0.001, 0.001
- **Top 5 Years**: 2023, 2023, 2023, 2023, 2023
- **Top 5 Categories**: personal, learning, saved, ai_ml, personal

#### Q08: What technical content is from 2022?

- **Type**: SPECIFIC
- **Latency**: 3991ms
- **Retrieved**: 15 docs
- **Year-matched**: 7
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.001, 0.001, 0.001, 0.001, 0.001
- **Top 5 Years**: 2022, 2022, 2022, 2022, 2022
- **Top 5 Categories**: ideas, saved, personal, ideas, philosophy

#### Q09: Show learning materials from 2020

- **Type**: SPECIFIC
- **Latency**: 7680ms
- **Retrieved**: 15 docs
- **Year-matched**: 13
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, learning, learning, learning, personal

#### Q10: What AI content do I have from 2025?

- **Type**: SPECIFIC
- **Latency**: 9326ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.005, 0.005, 0.005, 0.004
- **Top 5 Years**: 2025, 2025, 2025, 2025, 2025
- **Top 5 Categories**: personal, personal, saved, saved, learning

### MEDIUM Queries

#### Q11: How has my understanding of AI evolved over time?

- **Type**: TEMPORAL
- **Latency**: 8319ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2025, 2025, 2023, 2025
- **Top 5 Categories**: personal, learning, philosophy, learning, saved

#### Q12: What patterns connect my learning and personal growth?

- **Type**: SYNTHESIS
- **Latency**: 9425ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2020, 2025, 2020, 2022, 2023
- **Top 5 Categories**: learning, learning, learning, learning, ideas

#### Q13: Compare my interests in 2020 vs 2024

- **Type**: COMPARISON
- **Latency**: 6786ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.002, 0.002
- **Top 5 Years**: 2020, 2023, 2024, 2020, 2023
- **Top 5 Categories**: personal, personal, saved, ideas, saved

#### Q14: How do my technical notes relate to my project ideas?

- **Type**: SYNTHESIS
- **Latency**: 9402ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2023, 2024, 2024, 2020, 2024
- **Top 5 Categories**: learning, learning, learning, learning, saved

#### Q15: What have I learned about deep learning between 2021 and 2023?

- **Type**: TEMPORAL
- **Latency**: 4618ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.005, 0.004, 0.004, 0.004
- **Top 5 Years**: 2023, 2022, 2023, 2022, 2023
- **Top 5 Categories**: learning, ai_ml, learning, ai_ml, ai_ml

#### Q16: Show the progression of my saved articles over the years

- **Type**: TEMPORAL
- **Latency**: 4434ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2024, 2023, 2024, 2021, 2022
- **Top 5 Categories**: saved, saved, saved, saved, saved

#### Q17: What themes appear across my personal and philosophy notes?

- **Type**: SYNTHESIS
- **Latency**: 8496ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2022, 2023, 2020, 2024, 2023
- **Top 5 Categories**: saved, saved, personal, philosophy, personal

#### Q18: How has my approach to learning changed from 2020 to now?

- **Type**: TEMPORAL
- **Latency**: 8962ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.005, 0.004, 0.004, 0.004
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, personal, learning, ai_ml, saved

#### Q19: What connections exist between AI and philosophy in my notes?

- **Type**: SYNTHESIS
- **Latency**: 9161ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2022, 2025, 2025, 2023, 2024
- **Top 5 Categories**: philosophy, learning, learning, learning, philosophy

#### Q20: Compare technical approaches in 2021 vs 2023

- **Type**: COMPARISON
- **Latency**: 5765ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.002, 0.002, 0.002, 0.001
- **Top 5 Years**: 2023, 2021, 2023, 2023, 2022
- **Top 5 Categories**: personal, personal, philosophy, ai_ml, ideas

#### Q21: What ideas did I have that relate to machine learning?

- **Type**: SYNTHESIS
- **Latency**: 10190ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2022, 2020, 2020, 2025, 2023
- **Top 5 Categories**: ideas, learning, personal, personal, personal

#### Q22: How do my saved resources connect to my learning goals?

- **Type**: SYNTHESIS
- **Latency**: 7098ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2022, 2025, 2024, 2023, 2022
- **Top 5 Categories**: learning, saved, saved, saved, saved

#### Q23: What philosophical concepts influenced my technical work?

- **Type**: SYNTHESIS
- **Latency**: 8250ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.001, 0.001, 0.001
- **Top 5 Years**: 2025, 2021, 2021, 2022, 2025
- **Top 5 Categories**: personal, technical, ideas, saved, ideas

#### Q24: Track my understanding of transformers from 2020 to 2024

- **Type**: TEMPORAL
- **Latency**: 4069ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2023, 2023, 2023, 2023, 2020
- **Top 5 Categories**: learning, ai_ml, personal, personal, personal

#### Q25: What personal insights emerged from my technical challenges?

- **Type**: SYNTHESIS
- **Latency**: 4992ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2023, 2022, 2023, 2021, 2023
- **Top 5 Categories**: personal, personal, personal, technical, personal

#### Q26: How do my ideas evolve year by year?

- **Type**: TEMPORAL
- **Latency**: 6774ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2023, 2025, 2022, 2025, 2020
- **Top 5 Categories**: personal, ideas, ideas, ideas, personal

#### Q27: What saved articles influenced my project ideas?

- **Type**: SYNTHESIS
- **Latency**: 9621ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2025, 2024, 2022, 2023, 2024
- **Top 5 Categories**: saved, saved, saved, personal, saved

#### Q28: Compare my AI notes from early vs recent years

- **Type**: COMPARISON
- **Latency**: 9513ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2024, 2025, 2024, 2025
- **Top 5 Categories**: learning, learning, personal, saved, saved

#### Q29: What learning patterns emerge across all categories?

- **Type**: SYNTHESIS
- **Latency**: 9379ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.003, 0.003
- **Top 5 Years**: 2020, 2025, 2020, 2024, 2023
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q30: How has my focus shifted between technical and philosophical topics?

- **Type**: TEMPORAL
- **Latency**: 6823ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2023, 2020, 2022, 2022, 2022
- **Top 5 Categories**: ai_ml, saved, saved, saved, ideas

### HARD Queries

#### Q31: What patterns connect my learning, ideas, and personal growth across all years?

- **Type**: SYNTHESIS
- **Latency**: 10606ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2023, 2020, 2023, 2023, 2025
- **Top 5 Categories**: ideas, learning, ideas, philosophy, ideas

#### Q32: How do philosophical concepts influence my technical decision-making over time?

- **Type**: SYNTHESIS
- **Latency**: 10418ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2025, 2021, 2024, 2022, 2023
- **Top 5 Categories**: personal, ideas, saved, saved, ideas

#### Q33: Trace the evolution of my interests from 2020 to 2025

- **Type**: TEMPORAL
- **Latency**: 6777ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.004, 0.004, 0.004
- **Top 5 Years**: 2024, 2023, 2025, 2020, 2022
- **Top 5 Categories**: personal, personal, personal, personal, personal

#### Q34: What bird's eye view emerges from my entire knowledge base?

- **Type**: EXPLORATORY
- **Latency**: 6838ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2024, 2023, 2024, 2025, 2024
- **Top 5 Categories**: learning, learning, learning, ideas, learning

#### Q35: How do saved articles, personal reflections, and technical notes triangulate on key themes?

- **Type**: SYNTHESIS
- **Latency**: 10343ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2022, 2025, 2023, 2024, 2022
- **Top 5 Categories**: saved, saved, learning, saved, learning

#### Q36: What meta-patterns exist in how I approach learning across different domains?

- **Type**: EXPLORATORY
- **Latency**: 8535ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.003, 0.003
- **Top 5 Years**: 2020, 2024, 2023, 2022, 2020
- **Top 5 Categories**: learning, learning, learning, ideas, learning

#### Q37: Synthesize my understanding of AI ethics from technical, philosophical, and personal perspectives

- **Type**: SYNTHESIS
- **Latency**: 9149ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2024, 2023, 2025, 2023, 2023
- **Top 5 Categories**: philosophy, personal, personal, personal, saved

#### Q38: What hidden connections exist between seemingly unrelated categories?

- **Type**: EXPLORATORY
- **Latency**: 6774ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2025, 2022, 2022, 2022, 2021
- **Top 5 Categories**: learning, philosophy, ideas, philosophy, ai_ml

#### Q39: How has my worldview evolved through the synthesis of all my notes?

- **Type**: EXPLORATORY
- **Latency**: 8067ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2023, 2023, 2025, 2025
- **Top 5 Categories**: learning, learning, saved, saved, ai_ml

#### Q40: What comprehensive narrative emerges from my knowledge across time and domains?

- **Type**: EXPLORATORY
- **Latency**: 10408ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2025, 2022, 2022, 2024, 2025
- **Top 5 Categories**: saved, ideas, learning, saved, saved

#### Q41: Compare and contrast my approach to technical problems vs philosophical questions over time

- **Type**: COMPARISON
- **Latency**: 10453ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2025, 2020, 2023, 2025, 2023
- **Top 5 Categories**: ideas, learning, saved, saved, personal

#### Q42: What does my knowledge base reveal about my cognitive development from 2020-2025?

- **Type**: EXPLORATORY
- **Latency**: 5205ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.005, 0.005, 0.005, 0.004
- **Top 5 Years**: 2024, 2020, 2024, 2020, 2025
- **Top 5 Categories**: learning, learning, learning, ideas, personal

#### Q43: How do ideas flow between saved content, learning, and practical implementation?

- **Type**: SYNTHESIS
- **Latency**: 8460ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2025, 2025, 2024, 2022
- **Top 5 Categories**: learning, saved, ideas, learning, saved

#### Q44: What unifying themes connect disparate topics across my entire knowledge graph?

- **Type**: EXPLORATORY
- **Latency**: 7940ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2023, 2024, 2024, 2023, 2024
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q45: Analyze the feedback loops between my learning, reflection, and project ideas

- **Type**: SYNTHESIS
- **Latency**: 6632ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2025, 2025, 2023, 2020, 2021
- **Top 5 Categories**: ideas, saved, ai_ml, ideas, saved

#### Q46: What does the topology of my knowledge graph reveal about my thinking patterns?

- **Type**: EXPLORATORY
- **Latency**: 8628ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2025, 2023, 2020, 2025, 2024
- **Top 5 Categories**: personal, ai_ml, ideas, personal, saved

#### Q47: How do different temporal layers of my understanding interact and influence each other?

- **Type**: TEMPORAL
- **Latency**: 10168ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2020, 2021, 2024, 2023
- **Top 5 Categories**: philosophy, philosophy, ideas, learning, learning

#### Q48: Synthesize insights from hubs and bridges in my knowledge graph

- **Type**: EXPLORATORY
- **Latency**: 9972ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2023, 2023, 2024, 2025, 2023
- **Top 5 Categories**: learning, ai_ml, saved, saved, learning

#### Q49: What emergent properties arise from the cross-domain synthesis of my notes?

- **Type**: SYNTHESIS
- **Latency**: 7868ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.003, 0.002
- **Top 5 Years**: 2023, 2024, 2025, 2025, 2023
- **Top 5 Categories**: learning, learning, saved, saved, saved

#### Q50: Map the conceptual landscape of my entire knowledge ecosystem

- **Type**: EXPLORATORY
- **Latency**: 8504ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2021, 2023, 2024, 2024, 2025
- **Top 5 Categories**: ideas, saved, learning, personal, saved

## Visual Analysis

### Latency Distribution

```
Latency (ms) Distribution:
  3161-  3906 | █████ 1
  3906-  4650 | ████████████████████ 4
  4650-  5395 | ██████████ 2
  5395-  6139 | █████ 1
  6139-  6884 | ████████████████████████████████████████ 8
  6884-  7628 | ███████████████ 3
  7628-  8373 | ███████████████████████████████████ 7
  8373-  9117 | ████████████████████████████████████████ 8
  9117-  9862 | ████████████████████████████████████████ 8
  9862- 10606 | ████████████████████████████████████████ 8
```

### Retrieved Documents Distribution

```
# Documents Distribution:
    10-    10 | ██████████████████████████████ 16
    10-    11 |  0
    11-    12 |  0
    12-    12 |  0
    12-    12 | ████████████████████████ 13
    12-    13 |  0
    13-    14 |  0
    14-    14 |  0
    14-    14 |  0
    14-    15 | ████████████████████████████████████████ 21
```

