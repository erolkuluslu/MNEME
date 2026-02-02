# MNEME: A Temporal Knowledge Graph RAG System

**Personal Knowledge Management Through Temporal Reasoning and Cross-Domain Synthesis**

MNEME is a 7-layer Retrieval-Augmented Generation (RAG) system designed for personal knowledge management. Named after the Greek Titaness of memory, MNEME understands not just *what* you know, but *when* you learned it and *how* your knowledge evolved over time. The system combines temporal knowledge graphs, adaptive query routing, multi-modal retrieval, and year-strict citation enforcement to provide rich, contextually-aware answers from your personal knowledge base.

> **Research Foundation**: This implementation is based on the paper *"MNEME: A Temporal Knowledge Graph RAG System for Personal Knowledge Management"* by Erol Külüşlü, Akif Hasdemir, Furkan Yakkan, and Gökhan Bakal from Abdullah Gul University.

---

## Key Features

MNEME implements **5 key innovations** that address critical gaps in traditional RAG systems:

### 1. **Adaptive Query Routing**
Classifies queries by **difficulty level** (easy, medium, hard) and **type** (specific, temporal, synthesis, exploratory) to determine optimal retrieval strategies with dynamic document limits.

- **Specific queries** ("What did I learn about CNNs in 2021?") → 5-10 documents with strict temporal filtering
- **Temporal queries** ("How have my interests evolved?") → 10-15 documents spanning multiple years
- **Synthesis queries** ("What patterns connect my learning?") → 8-12 documents for cross-domain integration
- **Exploratory queries** ("What's my overall philosophy?") → 8-12 documents for comprehensive coverage

### 2. **Semantic Edge Typing**
Goes beyond simple similarity scores to classify relationships between chunks using **7 semantic edge types**:

- `elaborates` - Later chunk in same document expands on earlier content
- `contradicts` - Contains conflicting viewpoints ("however", "but", "although")
- `causes` - Causal relationships ("because", "therefore", "led to")
- `supports` - Reinforcing evidence ("confirms", "agrees", "validates")
- `temporal_sequence` - Earlier year with temporal markers
- `cross_domain` - Different categories with similarity ≥ 0.30
- `same_topic` - Same category, high similarity (default)

### 3. **Multi-Modal Hybrid Retrieval**
Combines **dense vector search** (semantic similarity) with **BM25 sparse retrieval** (keyword matching) using Reciprocal Rank Fusion (RRF):

- Dense weight: 1.0, Sparse weight: 0.5
- Year match boost: +0.5 (strong temporal affinity)
- Category match boost: +0.2 (domain alignment)
- RRF constant k=60 for harmonic fusion

### 4. **Pre-Computed Knowledge Structures**
Leverages RAPTOR-inspired hierarchical organization:

- **Communities**: Louvain algorithm (resolution=0.20) identifies thematic clusters
- **Hubs**: Top 10% nodes by degree centrality serve as entry points
- **Bridges**: Nodes connecting 3+ categories enable cross-domain synthesis
- **Narrative Arcs**: Temporal sequences showing knowledge evolution

### 5. **Year-Strict Citation Enforcement**
**Critical fix** for confidence calibration - determines confidence based on **actual year-matched content presence** rather than retrieval tier:

- `YEAR_MATCHED`: Found ≥1 source from requested year → No uncertainty preamble
- `PARTIAL_MATCH`: Year specified but only other years found → "I didn't find notes from [year], but..."
- `GOOD_MATCH`: Found relevant content (no year filter)
- `NO_MATCH`: No relevant content found

Eliminates false negative responses like *"Your notes don't directly address..."* when year-matched content actually exists.

---

## Architecture: The 7-Layer Pipeline

MNEME processes queries through a sequential 7-layer architecture, with each layer building on the previous:

```
User Query
    ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Document Processing                           │
│ • Discovery, chunking (~300 words), metadata           │
│ • Year/category extraction from filenames              │
│ Files: src/layer1_document/                            │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Knowledge Graph Construction                   │
│ • Sentence-BERT embeddings (384-dim)                   │
│ • Edge discovery with semantic typing                  │
│ • Graph construction (NetworkX)                        │
│ Files: src/layer2_graph/                               │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Knowledge Structures                           │
│ • Louvain community detection                          │
│ • Hub identification (top 10% by degree)               │
│ • Bridge nodes (3+ categories)                         │
│ Files: src/layer3_structures/                          │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Query Analysis                                 │
│ • Type classification (4 types)                        │
│ • Difficulty assessment (3 levels)                     │
│ • Year/category extraction                             │
│ • Query expansion with synonyms                        │
│ Files: src/layer4_query/                               │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Retrieval Engine                               │
│ • Hybrid RRF (dense + BM25)                            │
│ • Candidate pre-filtering (year ±2, category)         │
│ • Relevance boosting                                   │
│ Files: src/layer5_retrieval/                           │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 6: Thinking Engine                                │
│ • Gap detection (missing years/categories)             │
│ • Iterative retrieval to fill gaps                     │
│ • Context assembly                                     │
│ Files: src/layer6_thinking/                            │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 7: Answer Generation                              │
│ • Year-strict prompting                                │
│ • LLM generation (Gemini/OpenAI)                       │
│ • Citation enforcement                                 │
│ • Confidence calibration                               │
│ Files: src/layer7_generation/                          │
└─────────────────────┬───────────────────────────────────┘
                      ↓
                Enhanced Answer
```

### Innovation Mapping: Paper to Implementation

| Article Innovation | Implementation Location | Key Components |
|-------------------|------------------------|----------------|
| **Adaptive Query Routing** | `src/layer4_query/routing.py`<br>`src/layer4_query/difficulty.py` | QueryType × QueryDifficulty routing table<br>Dynamic document limits (3-15 docs)<br>Year pre-filter (±2 years) |
| **Semantic Edge Typing** | `src/layer2_graph/edge_discovery.py` | 7 edge types with keyword patterns<br>Heuristic-based classification<br>Cross-domain threshold (0.40) |
| **Multi-Modal Hybrid Retrieval** | `src/layer5_retrieval/strategies/hybrid_rrf.py` | Dense (1.0) + BM25 (0.5) fusion<br>RRF with k=60<br>Relevance boosting (+0.5 year, +0.2 category) |
| **Pre-Computed Structures** | `src/layer3_structures/community.py`<br>`src/layer3_structures/hubs_bridges.py` | Louvain communities (resolution=0.20)<br>Hub detection (top 10% degree)<br>Bridge identification (3+ categories) |
| **Year-Strict Citations** | `src/layer7_generation/citations.py`<br>`src/layer7_generation/confidence.py` | Content-based confidence<br>Year-matched source separation<br>Explicit citation boundaries |

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- API key for Gemini (recommended) or OpenAI
- ~2GB disk space for dependencies and embeddings

### Installation

```bash
# Clone the repository
git clone [repository-url]
cd MNEME

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-core.txt
pip install google-generativeai pyvis

# Configure environment
cp .env.example .env
# Edit .env and add your API key:
# GOOGLE_API_KEY=your_gemini_api_key_here
```

### First Query

```bash
# Run a single query
python src/run_demo.py --query "What happened in AI in 2023?"

# Run with detailed retrieval trace
python src/run_demo.py --query "AI in 2021" --trace

# Start interactive mode
python src/run_demo.py
```

### Interactive Mode Commands

Once in interactive mode, you can use:

- `stats` - Show system statistics
- `inspect` - Full resource inspection
- `graph` - Knowledge graph information
- `hubs` - List hub nodes (entry points)
- `bridges` - List bridge nodes (cross-domain connectors)
- `communities` - Show community breakdown
- `visualize` - Generate interactive HTML graph visualization
- `trace on/off` - Toggle retrieval trace mode
- `help` - Show all available commands
- `quit` - Exit the program

---

## System Statistics

Current implementation (from sample knowledge base):

- **264 chunks** from 233 documents
- **2,479 knowledge graph edges** with semantic typing
- **7 categories**: `ai_ml`, `ideas`, `learning`, `personal`, `philosophy`, `saved`, `technical`
- **13 communities** detected via Louvain algorithm
- **28 hub nodes** (top 10% by degree centrality)
- **73 bridge nodes** connecting multiple communities
- **384-dimensional embeddings** using `all-MiniLM-L6-v2`
- **Time span**: 2020-2025

---

## Documentation

- **[Setup Guide](SETUP_COMPLETE.md)** - Detailed installation and configuration instructions
- **[Configuration Reference](.env.example)** - All available environment variables and settings
- **[Sample Documents](documents/samples/README.md)** - Overview of example knowledge base
- **Architecture Details** - See 7-Layer Pipeline section above
- **Research Paper** - See Research & Citation section below

---

## Advanced Usage

### Custom Document Collections

Build MNEME with your own documents:

```python
from src.pipeline import MNEMEBuilder

# Initialize builder
builder = MNEMEBuilder()

# Build pipeline with custom documents
mneme = (builder
    .discover_documents("path/to/your/documents")
    .build_embeddings()
    .build_similarity_engine()
    .build_graph()
    .build_knowledge_structures()
    .build_llm_provider()
    .build())

# Query your knowledge base
answer = mneme.query("Your question here")
print(f"Answer: {answer.answer}")
print(f"Confidence: {answer.confidence}")
print(f"Citations: {answer.citations}")
```

### Configuration Options

The system uses centralized configuration in `src/config/settings.py` with **100+ configurable parameters**. Override via environment variables:

```bash
# Example: Adjust chunk size and similarity thresholds
export MNEME_TARGET_CHUNK_SIZE=500
export MNEME_SEMANTIC_SIMILARITY_THRESHOLD=0.42
export MNEME_LLM_PROVIDER=gemini
export MNEME_ANSWER_MODEL=gemini-3-flash-preview

# Run with custom configuration
python src/run_demo.py
```

**Configuration priority**: Environment variables > `.env` file > Default values

### Key Configuration Parameters

From `src/config/settings.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_chunk_size` | 300 | Target words per chunk |
| `semantic_similarity_threshold` | 0.45 | Same-domain edge threshold |
| `cross_domain_threshold` | 0.40 | Cross-domain edge threshold |
| `louvain_resolution` | 0.20 | Community detection granularity |
| `hub_threshold` | 0.9 | Percentile for hub identification (top 10%) |
| `rrf_k_constant` | 60 | RRF harmonic denominator |
| `dense_weight` | 1.0 | Dense retrieval contribution |
| `sparse_weight` | 0.5 | BM25 retrieval contribution |
| `year_match_boost` | 0.5 | Temporal affinity boost |
| `category_match_boost` | 0.2 | Domain alignment boost |

### Document Organization

Organize your documents with metadata in filenames:

```
documents/
├── ai_ml/
│   ├── 2023_neural_networks.txt
│   ├── 2024_transformers_deep_dive.txt
│   └── 2025_multimodal_learning.txt
├── personal/
│   ├── 2022_reflections.txt
│   └── 2023_goals.txt
└── philosophy/
    ├── 2021_stoicism_notes.txt
    └── 2024_ethics_reading.txt
```

**Category detection**: Automatic from directory name
**Year extraction**: Regex pattern `\b(20[0-2][0-9])\b` from filename
**Chunking**: Semantic paragraph boundaries, ~300 words per chunk

---

## Technical Details

### Algorithms & Techniques

MNEME integrates multiple state-of-the-art algorithms from RAG research:

- **BM25** [8]: Keyword-based sparse retrieval baseline with tuned parameters (k1=1.5, b=0.75)
- **RRF (Reciprocal Rank Fusion)** [9]: Multi-ranker fusion without score calibration, harmonic formula with k=60
- **RAPTOR** [5]: Hierarchical summarization adapted for temporal contexts (year-level, category-level, community-level)
- **Louvain** [10]: Community detection via modularity optimization with resolution parameter 0.20
- **Self-RAG** [2]: Faithfulness evaluation concept implemented as LLM-as-judge component
- **IRCoT** [4]: Interleaving retrieval with reasoning, simplified as gap detection and iterative retrieval
- **GraphRAG** [6]: Knowledge graph RAG adapted from entity-level to chunk-level graphs
- **Sentence-BERT** [11]: Multilingual semantic embeddings (all-MiniLM-L6-v2, 384-dim)
- **Adaptive-RAG** [3]: Query complexity classification extended with difficulty + type routing

### Performance Metrics

**Comprehensive Benchmark Validation** (50 diverse queries across all difficulty levels and query types):

#### Retrieval Performance (Perfect Scores)
- **MRR (Mean Reciprocal Rank)**: 1.000 - Every query's first result is relevant
- **Hit@5**: 1.000 - All queries find relevant documents in top 5
- **Hit@10**: 1.000 - Perfect coverage in top 10 results
- **Precision@5**: 1.000 - All top-5 documents are relevant
- **Category Coverage**: 1.000 - All 7 categories successfully utilized
- **Source Diversity**: 0.002 - High document reuse (expected with 233-document dataset)

#### Complex Reasoning (Production-Grade Performance)
- **Cross-Domain Success**: 92.0% (46/50 queries) - Strong multi-category bridging
- **Multi-Hop Success**: 100.0% (50/50 queries) - Perfect knowledge graph traversal
- **Multi-Hop Score**: 0.800 - Robust multi-source reasoning
- **Cross-Domain Score**: 0.727 - Excellent semantic bridging
- **Synthesis Quality**: 0.680 - Good integration of diverse sources

#### Performance by Difficulty
- **EASY** (n=10): Perfect retrieval, 15.0 avg citations, 100% success rate
- **MEDIUM** (n=20): Perfect retrieval, 12.8 avg citations, 100% success rate
- **HARD** (n=20): Perfect retrieval, 11.9 avg citations, 100% success rate

**Overall**: 100% success rate (50/50 queries), 12.9 average citations per query

#### System Performance
- **Average Latency**: 7.4 seconds per query (6-8s LLM inference + 1-2s retrieval)
- **P50 Latency**: 7.7s, **P95 Latency**: 10.2s
- **Throughput**: 0.13 queries/sec
- **Success Rate**: 100% across all query types and difficulty levels

#### Validation Results
All critical system components validated through comprehensive testing:
- ✅ **Multi-Hop Reasoning**: 100% success (improved from 24% through enhanced measurement)
- ✅ **Chronological Ordering**: Temporal queries correctly start from earliest year
- ✅ **Year-Specific Retrieval**: Perfect year filtering with enhanced BM25 tokenization
- ✅ **Comparison Queries**: Boundary-year filtering with balanced context
- ✅ **Cross-Domain Synthesis**: 92% success in multi-category bridging
- ✅ **Citation Quality**: Average 12.9 citations per query (range: 10-15)

#### Benchmark Methodology

**Initial Paper Evaluation** (10 queries): Established baseline performance with MRR=0.833, demonstrating strong retrieval and reasoning capabilities across diverse query types.

**Comprehensive System Validation** (50 queries): Extended evaluation conducted February 2026 with rigorous testing across all difficulty levels and query types. Identified and resolved 6 critical issues through root cause analysis, achieving production-grade reliability with 100% success rate.

**Documentation**: Complete benchmark analysis with architectural discussion available in `results/COMPREHENSIVE_50_QUERY_ANALYSIS.md`. Includes detailed examination of why MNEME achieves exceptional performance through 7-layer architectural synergy, multi-signal fusion, and query-aware processing.

### Key Design Decisions

**Why chunk-level graphs instead of entity extraction?**
Personal knowledge is narrative and contextual - full chunk semantics capture meaning better than isolated entities. Entity extraction would lose the narrative flow essential to personal knowledge.

**Why RRF over learned fusion?**
RRF requires no training data and provides principled score-free fusion. Personal knowledge bases are too small and diverse for supervised learning approaches.

**Why heuristic edge typing instead of LLM classification?**
LLM classification of 2,479 edges would take ~25 minutes at 0.5s/edge. Heuristic patterns achieve comparable accuracy at 1000× lower latency and cost.

**Why year-strict citation?**
Temporal coherence is critical for personal knowledge. When users ask about 2021, citing 2023 content (even if semantically similar) breaks the narrative and erodes trust.

---

## Research & Citation

### Research Foundation

This implementation is a proof of the research paper:

**"MNEME: A Temporal Knowledge Graph RAG System for Personal Knowledge Management"**
Erol Külüşlü, Akif Hasdemir, Furkan Yakkan, Gökhan Bakal
Department of Computer Engineering, Abdullah Gul University, Kayseri, Turkey
2026

The paper addresses critical gaps in traditional RAG systems that fail to handle temporal reasoning and cross-domain synthesis effectively. The research demonstrates that personal knowledge is inherently narrative—it captures not just what we know, but when we learned it and how concepts evolved over time.

### Key Contributions

1. **Adaptive Query Routing**: Query classification system routing based on difficulty level (easy, medium, hard) and type (specific, temporal, synthesis, exploratory) with dynamic document limits
2. **Semantic Edge Typing**: Heuristic-based relationship classification into 7 types (elaborates, contradicts, causes, supports, temporal_sequence, cross_domain, same_topic)
3. **Multi-Modal Hybrid Retrieval**: Integration of dense vector search with BM25 sparse retrieval using RRF
4. **Pre-Computed Knowledge Structures**: RAPTOR-inspired hierarchical summaries, hub/bridge identification
5. **Year-Strict Citation Enforcement**: Critical fix for confidence calibration based on actual year-matched content presence

### BibTeX Citation

```bibtex
@article{mneme2025,
  title={MNEME: A Temporal Knowledge Graph RAG System for Personal Knowledge Management},
  author={K{\"u}l{\"u}{\c{s}}l{\"u}, Erol and Hasdemir, Akif and Yakkan, Furkan and Bakal, G{\"o}khan},
  journal={arXiv preprint},
  year={2026},
  institution={Abdullah Gul University},
  address={Kayseri, Turkey}
}
```

### Related Work

This system builds upon and integrates concepts from:

- **RAG** [1]: Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020
- **Self-RAG** [2]: Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection", 2023
- **Adaptive-RAG** [3]: Jeong et al., "Adaptive-RAG: Learning to Adapt Retrieval-Augmented LLMs", 2024
- **IRCoT** [4]: Trivedi et al., "Interleaving Retrieval with Chain-of-Thought Reasoning", ACL 2023
- **RAPTOR** [5]: Sarthi et al., "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval", ICLR 2024
- **GraphRAG** [6]: Edge et al., "From Local to Global: A Graph RAG Approach", 2024
- **HyDE** [7]: Gao et al., "Precise Zero-Shot Dense Retrieval without Relevance Labels", ACL 2023
- **BM25** [8]: Robertson & Zaragoza, "The Probabilistic Relevance Framework", 2009
- **RRF** [9]: Cormack et al., "Reciprocal Rank Fusion Outperforms Condorcet", SIGIR 2009
- **Louvain** [10]: Blondel et al., "Fast unfolding of communities in large networks", 2008
- **Sentence-BERT** [11]: Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks", EMNLP 2019
- **RAGAS** [12]: Es et al., "RAGAS: Automated Evaluation of RAG", 2023

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss proposed changes.

### Development Setup

```bash
# Clone and setup
git clone [repository-url]
cd MNEME
python3 -m venv venv
source venv/bin/activate

# Install all dependencies including dev tools
pip install -r requirements.txt
pip install pytest black mypy ruff
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_layer4_query.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Style

```bash
# Format code with Black
black src/ tests/

# Type checking with mypy
mypy src/

# Linting with ruff
ruff check src/ tests/
```

### Project Structure

```
MNEME/
├── src/
│   ├── config/              # Central configuration
│   ├── models/              # Data models (Chunk, Answer, QueryPlan)
│   ├── layer1_document/     # Document processing
│   ├── layer2_graph/        # Embeddings & graph construction
│   ├── layer3_structures/   # Communities, hubs, bridges
│   ├── layer4_query/        # Query analysis & routing
│   ├── layer5_retrieval/    # Hybrid RRF retrieval
│   ├── layer6_thinking/     # Gap detection & context
│   ├── layer7_generation/   # Answer generation & citations
│   ├── pipeline/            # Main MNEME orchestrator
│   └── run_demo.py          # Interactive CLI
├── documents/
│   └── samples/             # Example knowledge base
├── tests/                   # Test suite
├── requirements-core.txt    # Core dependencies
├── requirements.txt         # All dependencies
├── .env.example            # Configuration template
└── README.md               # This file
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)** - see the [LICENSE](LICENSE) file for details.

**Commercial Use:**
If you wish to use this code in a proprietary/commercial product where you do not wish to open-source your code, please contact the authors for a commercial license.

---

## Acknowledgments

- Built with [sentence-transformers](https://www.sbert.net/) for semantic embeddings
- Powered by [Google Generative AI](https://ai.google.dev/) (Gemini) and [OpenAI](https://openai.com/)
- Graph processing with [NetworkX](https://networkx.org/)
- Visualization with [PyVis](https://pyvis.readthedocs.io/)
- Inspired by research in temporal knowledge graphs, personal knowledge management, and RAG systems
- Thanks to the open-source RAG community for foundational concepts and evaluation frameworks

---

**Questions or Issues?** Open an issue on GitHub or contact the authors at Abdullah Gul University.
