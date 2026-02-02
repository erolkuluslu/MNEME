# MNEME Comprehensive Benchmark Results

**Date**: 2026-02-02 11:50:24
**Queries**: 50
**Success Rate**: 100.0%

---

## Executive Summary

Benchmarked MNEME with **50 diverse queries** across 3 difficulty levels and 5 query types.

### Key Findings

- **Success Rate**: 50/50 (100.0%)
- **Average Latency**: 7413ms
- **Median Latency**: 7724ms
- **P95 Latency**: 10390ms
- **Cross-Domain Success**: 50/27 (185.2%)
- **Multi-Hop Success**: 12/12 (100.0%)

## Performance by Difficulty

| Difficulty | Queries | Avg Latency (ms) | Avg Retrieved | Avg Confidence |
|-----------|---------|------------------|---------------|----------------|
| EASY | 10 | 6068 | 15.0 | 0.0% |
| MEDIUM | 20 | 7239 | 12.8 | 0.0% |
| HARD | 20 | 8260 | 11.9 | 0.0% |

## Performance by Query Type

| Type | Queries | Avg Latency (ms) | Avg Retrieved | Cross-Domain % |
|------|---------|------------------|---------------|----------------|
| SPECIFIC | 10 | 6068 | 15.0 | 100.0% |
| TEMPORAL | 9 | 6457 | 14.1 | 100.0% |
| SYNTHESIS | 17 | 8602 | 11.8 | 100.0% |
| COMPARISON | 4 | 7466 | 15.0 | 100.0% |
| EXPLORATORY | 10 | 7577 | 10.9 | 100.0% |

## Detailed Query Results

### EASY Queries

#### Q01: What did I learn about neural networks in 2021?

- **Type**: SPECIFIC
- **Latency**: 4372ms
- **Retrieved**: 15 docs
- **Year-matched**: 12
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.001, 0.001, 0.001
- **Top 5 Years**: 2021, 2021, 2021, 2021, 2021
- **Top 5 Categories**: technical, personal, learning, philosophy, personal

#### Q02: Show me my notes from 2023 about transformers

- **Type**: SPECIFIC
- **Latency**: 5444ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2023, 2023, 2023, 2023, 2023
- **Top 5 Categories**: learning, ai_ml, ideas, learning, personal

#### Q03: What are my personal reflections from 2022?

- **Type**: SPECIFIC
- **Latency**: 7511ms
- **Retrieved**: 15 docs
- **Year-matched**: 11
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.002, 0.002, 0.002
- **Top 5 Years**: 2022, 2022, 2022, 2022, 2022
- **Top 5 Categories**: saved, saved, learning, ideas, ideas

#### Q04: What did I save about Python in 2020?

- **Type**: SPECIFIC
- **Latency**: 2060ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, ideas, personal, saved, personal

#### Q05: Show notes about machine learning from 2024

- **Type**: SPECIFIC
- **Latency**: 6269ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2024, 2024, 2024, 2024, 2024
- **Top 5 Categories**: personal, learning, ai_ml, personal, learning

#### Q06: What ideas did I have in 2021?

- **Type**: SPECIFIC
- **Latency**: 6726ms
- **Retrieved**: 15 docs
- **Year-matched**: 13
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2021, 2021, 2021, 2021, 2021
- **Top 5 Categories**: personal, learning, technical, philosophy, personal

#### Q07: Find my philosophy notes from 2023

- **Type**: SPECIFIC
- **Latency**: 7564ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2023, 2023, 2023, 2023
- **Top 5 Categories**: personal, learning, personal, ai_ml, saved

#### Q08: What technical content is from 2022?

- **Type**: SPECIFIC
- **Latency**: 5661ms
- **Retrieved**: 15 docs
- **Year-matched**: 13
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2022, 2022, 2022, 2022, 2022
- **Top 5 Categories**: learning, learning, learning, saved, learning

#### Q09: Show learning materials from 2020

- **Type**: SPECIFIC
- **Latency**: 6775ms
- **Retrieved**: 15 docs
- **Year-matched**: 14
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, learning, personal, personal, learning

#### Q10: What AI content do I have from 2025?

- **Type**: SPECIFIC
- **Latency**: 8294ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.005, 0.005, 0.005, 0.005, 0.005
- **Top 5 Years**: 2025, 2025, 2025, 2025, 2025
- **Top 5 Categories**: personal, personal, saved, learning, learning

### MEDIUM Queries

#### Q11: How has my understanding of AI evolved over time?

- **Type**: TEMPORAL
- **Latency**: 8513ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2020, 2022, 2023, 2023, 2023
- **Top 5 Categories**: philosophy, philosophy, personal, learning, saved

#### Q12: What patterns connect my learning and personal growth?

- **Type**: SYNTHESIS
- **Latency**: 9390ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2020, 2025, 2025, 2023, 2023
- **Top 5 Categories**: learning, learning, saved, learning, personal

#### Q13: Compare my interests in 2020 vs 2024

- **Type**: COMPARISON
- **Latency**: 6754ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2024, 2024, 2020, 2022, 2020
- **Top 5 Categories**: saved, ideas, ideas, saved, personal

#### Q14: How do my technical notes relate to my project ideas?

- **Type**: SYNTHESIS
- **Latency**: 9286ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2023, 2024, 2024, 2022, 2020
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q15: What have I learned about deep learning between 2021 and 2023?

- **Type**: TEMPORAL
- **Latency**: 3547ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.004, 0.002, 0.002
- **Top 5 Years**: 2023, 2023, 2023, 2021, 2023
- **Top 5 Categories**: learning, learning, personal, technical, ideas

#### Q16: Show the progression of my saved articles over the years

- **Type**: TEMPORAL
- **Latency**: 5416ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2021, 2021, 2022, 2022
- **Top 5 Categories**: personal, saved, ideas, personal, saved

#### Q17: What themes appear across my personal and philosophy notes?

- **Type**: SYNTHESIS
- **Latency**: 8427ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2025, 2024, 2020, 2023, 2022
- **Top 5 Categories**: saved, learning, saved, learning, saved

#### Q18: How has my approach to learning changed from 2020 to now?

- **Type**: TEMPORAL
- **Latency**: 6916ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.006, 0.005, 0.005, 0.004, 0.002
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, learning, learning, ideas, learning

#### Q19: What connections exist between AI and philosophy in my notes?

- **Type**: SYNTHESIS
- **Latency**: 8886ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2025, 2023, 2025, 2025, 2024
- **Top 5 Categories**: learning, learning, saved, personal, philosophy

#### Q20: Compare technical approaches in 2021 vs 2023

- **Type**: COMPARISON
- **Latency**: 4891ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2023, 2022, 2023, 2023, 2023
- **Top 5 Categories**: personal, saved, saved, ai_ml, personal

#### Q21: What ideas did I have that relate to machine learning?

- **Type**: SYNTHESIS
- **Latency**: 8903ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2024, 2025, 2025, 2025, 2024
- **Top 5 Categories**: learning, personal, personal, personal, personal

#### Q22: How do my saved resources connect to my learning goals?

- **Type**: SYNTHESIS
- **Latency**: 8136ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2022, 2025, 2022, 2023, 2024
- **Top 5 Categories**: ideas, saved, saved, learning, learning

#### Q23: What philosophical concepts influenced my technical work?

- **Type**: SYNTHESIS
- **Latency**: 7995ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2025, 2023, 2024, 2021, 2021
- **Top 5 Categories**: personal, ideas, philosophy, technical, ideas

#### Q24: Track my understanding of transformers from 2020 to 2024

- **Type**: TEMPORAL
- **Latency**: 2878ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2023, 2023, 2024, 2021, 2021
- **Top 5 Categories**: learning, personal, personal, learning, ideas

#### Q25: What personal insights emerged from my technical challenges?

- **Type**: SYNTHESIS
- **Latency**: 5057ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2025, 2025, 2023, 2024
- **Top 5 Categories**: personal, saved, personal, personal, personal

#### Q26: How do my ideas evolve year by year?

- **Type**: TEMPORAL
- **Latency**: 7354ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2022, 2023, 2023, 2020, 2025
- **Top 5 Categories**: ideas, personal, personal, ideas, saved

#### Q27: What saved articles influenced my project ideas?

- **Type**: SYNTHESIS
- **Latency**: 6756ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2025, 2024, 2024, 2022, 2025
- **Top 5 Categories**: saved, learning, saved, saved, saved

#### Q28: Compare my AI notes from early vs recent years

- **Type**: COMPARISON
- **Latency**: 8210ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2022, 2023, 2024, 2025, 2023
- **Top 5 Categories**: saved, learning, learning, personal, personal

#### Q29: What learning patterns emerge across all categories?

- **Type**: SYNTHESIS
- **Latency**: 8716ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.003, 0.003, 0.002
- **Top 5 Years**: 2025, 2024, 2023, 2020, 2023
- **Top 5 Categories**: learning, learning, learning, learning, ideas

#### Q30: How has my focus shifted between technical and philosophical topics?

- **Type**: TEMPORAL
- **Latency**: 8750ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2022, 2023, 2020, 2021, 2021
- **Top 5 Categories**: ideas, learning, learning, ideas, learning

### HARD Queries

#### Q31: What patterns connect my learning, ideas, and personal growth across all years?

- **Type**: SYNTHESIS
- **Latency**: 10318ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2020, 2025, 2023, 2025, 2025
- **Top 5 Categories**: learning, saved, ideas, learning, ideas

#### Q32: How do philosophical concepts influence my technical decision-making over time?

- **Type**: SYNTHESIS
- **Latency**: 9343ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2022, 2022, 2023, 2025
- **Top 5 Categories**: ideas, ideas, saved, ideas, ideas

#### Q33: Trace the evolution of my interests from 2020 to 2025

- **Type**: TEMPORAL
- **Latency**: 5216ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.002, 0.004
- **Top 5 Years**: 2020, 2020, 2020, 2022, 2023
- **Top 5 Categories**: saved, ideas, personal, ideas, saved

#### Q34: What bird's eye view emerges from my entire knowledge base?

- **Type**: EXPLORATORY
- **Latency**: 6424ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2024, 2025, 2021, 2021
- **Top 5 Categories**: learning, learning, personal, learning, technical

#### Q35: How do saved articles, personal reflections, and technical notes triangulate on key themes?

- **Type**: SYNTHESIS
- **Latency**: 10793ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2022, 2023, 2020, 2024, 2025
- **Top 5 Categories**: saved, learning, learning, learning, saved

#### Q36: What meta-patterns exist in how I approach learning across different domains?

- **Type**: EXPLORATORY
- **Latency**: 7056ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.004, 0.004, 0.004
- **Top 5 Years**: 2020, 2023, 2024, 2025, 2024
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q37: Synthesize my understanding of AI ethics from technical, philosophical, and personal perspectives

- **Type**: SYNTHESIS
- **Latency**: 9758ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2024, 2025, 2023, 2022, 2025
- **Top 5 Categories**: philosophy, personal, personal, philosophy, saved

#### Q38: What hidden connections exist between seemingly unrelated categories?

- **Type**: EXPLORATORY
- **Latency**: 7787ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2024, 2025, 2022, 2023, 2025
- **Top 5 Categories**: learning, learning, philosophy, learning, ideas

#### Q39: How has my worldview evolved through the synthesis of all my notes?

- **Type**: EXPLORATORY
- **Latency**: 7665ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2023, 2024, 2022, 2024, 2022
- **Top 5 Categories**: learning, learning, saved, personal, ideas

#### Q40: What comprehensive narrative emerges from my knowledge across time and domains?

- **Type**: EXPLORATORY
- **Latency**: 10478ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.002, 0.002, 0.002, 0.002
- **Top 5 Years**: 2025, 2025, 2022, 2025, 2022
- **Top 5 Categories**: personal, saved, ideas, saved, learning

#### Q41: Compare and contrast my approach to technical problems vs philosophical questions over time

- **Type**: COMPARISON
- **Latency**: 10008ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2022, 2023, 2025, 2025, 2022
- **Top 5 Categories**: saved, saved, saved, ideas, ideas

#### Q42: What does my knowledge base reveal about my cognitive development from 2020-2025?

- **Type**: EXPLORATORY
- **Latency**: 5767ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.006, 0.004, 0.002, 0.002, 0.002
- **Top 5 Years**: 2020, 2020, 2020, 2022, 2023
- **Top 5 Categories**: learning, ideas, learning, learning, learning

#### Q43: How do ideas flow between saved content, learning, and practical implementation?

- **Type**: SYNTHESIS
- **Latency**: 9611ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.003
- **Top 5 Years**: 2023, 2024, 2023, 2022, 2024
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q44: What unifying themes connect disparate topics across my entire knowledge graph?

- **Type**: EXPLORATORY
- **Latency**: 7783ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.004, 0.004, 0.004, 0.003
- **Top 5 Years**: 2023, 2024, 2023, 2024, 2023
- **Top 5 Categories**: learning, learning, learning, learning, ideas

#### Q45: Analyze the feedback loops between my learning, reflection, and project ideas

- **Type**: SYNTHESIS
- **Latency**: 9851ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2025, 2024, 2023, 2024, 2025
- **Top 5 Categories**: learning, learning, learning, learning, ideas

#### Q46: What does the topology of my knowledge graph reveal about my thinking patterns?

- **Type**: EXPLORATORY
- **Latency**: 4641ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.002, 0.002
- **Top 5 Years**: 2025, 2023, 2021, 2023, 2022
- **Top 5 Categories**: personal, ideas, learning, personal, saved

#### Q47: How do different temporal layers of my understanding interact and influence each other?

- **Type**: TEMPORAL
- **Latency**: 9520ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.003, 0.003, 0.003, 0.003, 0.002
- **Top 5 Years**: 2024, 2023, 2020, 2023, 2020
- **Top 5 Categories**: learning, learning, learning, learning, learning

#### Q48: Synthesize insights from hubs and bridges in my knowledge graph

- **Type**: EXPLORATORY
- **Latency**: 9642ms
- **Retrieved**: 12 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 12
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.002, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2023, 2023, 2021, 2023, 2024
- **Top 5 Categories**: learning, ai_ml, personal, learning, learning

#### Q49: What emergent properties arise from the cross-domain synthesis of my notes?

- **Type**: SYNTHESIS
- **Latency**: 5011ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.003, 0.002, 0.002, 0.002
- **Top 5 Years**: 2023, 2024, 2025, 2022, 2024
- **Top 5 Categories**: learning, learning, saved, saved, saved

#### Q50: Map the conceptual landscape of my entire knowledge ecosystem

- **Type**: EXPLORATORY
- **Latency**: 8525ms
- **Retrieved**: 10 docs
- **Year-matched**: 0
- **Confidence**: good_match
- **Citations**: 10
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.004, 0.002, 0.002, 0.001, 0.001
- **Top 5 Years**: 2021, 2023, 2024, 2025, 2021
- **Top 5 Categories**: ideas, saved, learning, ai_ml, ideas

## Visual Analysis

### Latency Distribution

```
Latency (ms) Distribution:
  2060-  2933 | ████████ 2
  2933-  3806 | ████ 1
  3806-  4680 | ████████ 2
  4680-  5553 | ██████████████████████████ 6
  5553-  6426 | █████████████████ 4
  6426-  7300 | ██████████████████████████ 6
  7300-  8173 | ███████████████████████████████████ 8
  8173-  9047 | ████████████████████████████████████████ 9
  9047-  9920 | ███████████████████████████████████ 8
  9920- 10793 | █████████████████ 4
```

### Retrieved Documents Distribution

```
# Documents Distribution:
    10-    10 | █████████████████████ 13
    10-    11 |  0
    11-    12 |  0
    12-    12 |  0
    12-    12 | █████████████████████ 13
    12-    13 |  0
    13-    14 |  0
    14-    14 |  0
    14-    14 |  0
    14-    15 | ████████████████████████████████████████ 24
```

