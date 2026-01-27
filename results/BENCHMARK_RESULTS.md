# MNEME Comprehensive Benchmark Results

**Date**: 2026-01-27 09:50:31
**Queries**: 10
**Success Rate**: 100.0%

---

## Executive Summary

Benchmarked MNEME with **10 diverse queries** across 3 difficulty levels and 5 query types.

### Key Findings

- **Success Rate**: 10/10 (100.0%)
- **Average Latency**: 4455ms
- **Median Latency**: 3756ms
- **P95 Latency**: 8596ms
- **Cross-Domain Success**: 10/0 (0.0%)
- **Multi-Hop Success**: 0/0 (0.0%)

## Performance by Difficulty

| Difficulty | Queries | Avg Latency (ms) | Avg Retrieved | Avg Confidence |
|-----------|---------|------------------|---------------|----------------|
| EASY | 10 | 4455 | 15.0 | 0.0% |

## Performance by Query Type

| Type | Queries | Avg Latency (ms) | Avg Retrieved | Cross-Domain % |
|------|---------|------------------|---------------|----------------|
| SPECIFIC | 10 | 4455 | 15.0 | 100.0% |

## Detailed Query Results

### EASY Queries

#### Q01: What did I learn about neural networks in 2021?

- **Type**: SPECIFIC
- **Latency**: 3328ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.803, 0.672, 0.668, 0.619, 0.585
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, ai_ml, personal, ai_ml, personal

#### Q02: Show me my notes from 2023 about transformers

- **Type**: SPECIFIC
- **Latency**: 5308ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.605, 0.549, 0.515, 0.354, 0.323
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: ai_ml, learning, personal, learning, learning

#### Q03: What are my personal reflections from 2022?

- **Type**: SPECIFIC
- **Latency**: 2938ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.718, 0.682, 0.610, 0.527, 0.524
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, saved, personal, personal, personal

#### Q04: What did I save about Python in 2020?

- **Type**: SPECIFIC
- **Latency**: 5358ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.925, 0.667, 0.544, 0.474, 0.450
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, ai_ml, personal, learning, personal

#### Q05: Show notes about machine learning from 2024

- **Type**: SPECIFIC
- **Latency**: 3127ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.681, 0.645, 0.624, 0.577, 0.556
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, ai_ml, ai_ml, personal, learning

#### Q06: What ideas did I have in 2021?

- **Type**: SPECIFIC
- **Latency**: 2942ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.750, 0.659, 0.579, 0.568, 0.456
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: ideas, ideas, saved, ideas, personal

#### Q07: Find my philosophy notes from 2023

- **Type**: SPECIFIC
- **Latency**: 5440ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.724, 0.622, 0.571, 0.546, 0.514
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, saved, learning, saved, learning

#### Q08: What technical content is from 2022?

- **Type**: SPECIFIC
- **Latency**: 3789ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.533, 0.450, 0.405, 0.399, 0.367
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: learning, saved, learning, personal, personal

#### Q09: Show learning materials from 2020

- **Type**: SPECIFIC
- **Latency**: 8596ms
- **Retrieved**: 15 docs
- **Year-matched**: 15
- **Confidence**: year_matched
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 1.024, 0.936, 0.895, 0.867, 0.729
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, ai_ml, personal, personal, learning

#### Q10: What AI content do I have from 2025?

- **Type**: SPECIFIC
- **Latency**: 3723ms
- **Retrieved**: 15 docs
- **Year-matched**: 0
- **Confidence**: partial_match
- **Citations**: 15
- **Cross-domain**: Yes
- **Top 5 Scores**: 0.713, 0.709, 0.657, 0.638, 0.628
- **Top 5 Years**: 2020, 2020, 2020, 2020, 2020
- **Top 5 Categories**: personal, personal, learning, saved, saved

## Visual Analysis

### Latency Distribution

```
Latency (ms) Distribution:
  2938-  3504 | ████████████████████████████████████████ 4
  3504-  4070 | ████████████████████ 2
  4070-  4635 |  0
  4635-  5201 |  0
  5201-  5767 | ██████████████████████████████ 3
  5767-  6333 |  0
  6333-  6898 |  0
  6898-  7464 |  0
  7464-  8030 |  0
  8030-  8596 | ██████████ 1
```

### Retrieved Documents Distribution

```
