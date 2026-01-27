"""
Tests for Adaptive Router

TDD tests for Phase A: Adaptive Query Routing.
Tests routing decisions based on query type and difficulty.
"""

import pytest

from src.models.query import QueryPlan, QueryType, QueryFilters, QueryExpansion


class TestAdaptiveRouter:
    """Tests for AdaptiveRouter."""

    @pytest.fixture
    def router(self):
        """Create an AdaptiveRouter instance."""
        from src.layer4_query.routing import AdaptiveRouter
        return AdaptiveRouter()

    @pytest.fixture
    def make_plan_for_routing(self, make_query_plan):
        """Factory for creating plans with specific type and complexity."""
        def _make(
            query_type: QueryType,
            complexity_score: float,
            year_filter: int = None,
        ) -> QueryPlan:
            return make_query_plan(
                query="Test query",
                query_type=query_type,
                complexity_score=complexity_score,
                year_filter=year_filter,
            )
        return _make

    # =========================================================================
    # SPECIFIC Query Type Routing Tests
    # =========================================================================

    def test_route_specific_easy_returns_3_5_docs(self, router, make_plan_for_routing):
        """SPECIFIC + EASY → 3-5 docs."""
        from src.layer4_query.routing import RoutingDecision

        plan = make_plan_for_routing(QueryType.SPECIFIC, 0.2)  # EASY
        decision = router.route(plan)

        assert isinstance(decision, RoutingDecision)
        assert decision.min_docs == 3
        assert decision.max_docs == 5

    def test_route_specific_medium_returns_5_8_docs(self, router, make_plan_for_routing):
        """SPECIFIC + MEDIUM → 5-8 docs."""
        plan = make_plan_for_routing(QueryType.SPECIFIC, 0.5)  # MEDIUM
        decision = router.route(plan)

        assert decision.min_docs == 5
        assert decision.max_docs == 8

    def test_route_specific_hard_returns_5_10_docs(self, router, make_plan_for_routing):
        """SPECIFIC + HARD → 5-10 docs."""
        plan = make_plan_for_routing(QueryType.SPECIFIC, 0.75)  # HARD
        decision = router.route(plan)

        assert decision.min_docs == 5
        assert decision.max_docs == 10

    # =========================================================================
    # TEMPORAL Query Type Routing Tests
    # =========================================================================

    def test_route_temporal_easy_returns_5_8_docs(self, router, make_plan_for_routing):
        """TEMPORAL + EASY → 5-8 docs."""
        plan = make_plan_for_routing(QueryType.TEMPORAL, 0.2)  # EASY
        decision = router.route(plan)

        assert decision.min_docs == 5
        assert decision.max_docs == 8

    def test_route_temporal_medium_returns_8_12_docs(self, router, make_plan_for_routing):
        """TEMPORAL + MEDIUM → 8-12 docs."""
        plan = make_plan_for_routing(QueryType.TEMPORAL, 0.5)  # MEDIUM
        decision = router.route(plan)

        assert decision.min_docs == 8
        assert decision.max_docs == 12

    def test_route_temporal_hard_returns_10_15_docs(self, router, make_plan_for_routing):
        """TEMPORAL + HARD → 10-15 docs."""
        plan = make_plan_for_routing(QueryType.TEMPORAL, 0.75)  # HARD
        decision = router.route(plan)

        assert decision.min_docs == 10
        assert decision.max_docs == 15

    # =========================================================================
    # SYNTHESIS Query Type Routing Tests
    # =========================================================================

    def test_route_synthesis_easy_returns_6_10_docs(self, router, make_plan_for_routing):
        """SYNTHESIS + EASY → 6-10 docs."""
        plan = make_plan_for_routing(QueryType.SYNTHESIS, 0.2)  # EASY
        decision = router.route(plan)

        assert decision.min_docs == 6
        assert decision.max_docs == 10

    def test_route_synthesis_medium_returns_8_12_docs(self, router, make_plan_for_routing):
        """SYNTHESIS + MEDIUM → 8-12 docs."""
        plan = make_plan_for_routing(QueryType.SYNTHESIS, 0.5)  # MEDIUM
        decision = router.route(plan)

        assert decision.min_docs == 8
        assert decision.max_docs == 12

    def test_route_synthesis_hard_returns_10_15_docs(self, router, make_plan_for_routing):
        """SYNTHESIS + HARD → 10-15 docs."""
        plan = make_plan_for_routing(QueryType.SYNTHESIS, 0.75)  # HARD
        decision = router.route(plan)

        assert decision.min_docs == 10
        assert decision.max_docs == 15

    # =========================================================================
    # Year Pre-filter Tests
    # =========================================================================

    def test_route_with_year_filter_enables_prefiltering(self, router, make_plan_for_routing):
        """Year filter should enable pre-filtering with ±2 year range."""
        plan = make_plan_for_routing(QueryType.TEMPORAL, 0.5, year_filter=2021)
        decision = router.route(plan)

        assert decision.year_prefilter_range == 2

    def test_route_without_year_filter_disables_prefiltering(self, router, make_plan_for_routing):
        """No year filter should disable pre-filtering."""
        plan = make_plan_for_routing(QueryType.SPECIFIC, 0.5, year_filter=None)
        decision = router.route(plan)

        assert decision.year_prefilter_range == 0

    # =========================================================================
    # RoutingDecision Structure Tests
    # =========================================================================

    def test_routing_decision_has_difficulty(self, router, make_plan_for_routing):
        """RoutingDecision should include the classified difficulty."""
        from src.layer4_query.difficulty import QueryDifficulty
        from src.layer4_query.routing import RoutingDecision

        plan = make_plan_for_routing(QueryType.SPECIFIC, 0.2)
        decision = router.route(plan)

        assert hasattr(decision, "difficulty")
        assert decision.difficulty == QueryDifficulty.EASY

    def test_routing_decision_has_all_required_fields(self, router, make_plan_for_routing):
        """RoutingDecision should have all required fields."""
        plan = make_plan_for_routing(QueryType.TEMPORAL, 0.5)
        decision = router.route(plan)

        assert hasattr(decision, "difficulty")
        assert hasattr(decision, "min_docs")
        assert hasattr(decision, "max_docs")
        assert hasattr(decision, "year_prefilter_range")

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_route_comparison_query(self, router, make_plan_for_routing):
        """COMPARISON queries should have reasonable defaults."""
        plan = make_plan_for_routing(QueryType.COMPARISON, 0.5)
        decision = router.route(plan)

        # Should have sensible min/max
        assert decision.min_docs >= 5
        assert decision.max_docs >= decision.min_docs

    def test_route_exploratory_query(self, router, make_plan_for_routing):
        """EXPLORATORY queries should have reasonable defaults."""
        plan = make_plan_for_routing(QueryType.EXPLORATORY, 0.5)
        decision = router.route(plan)

        # Should have sensible min/max
        assert decision.min_docs >= 5
        assert decision.max_docs >= decision.min_docs


class TestRoutingTableCoverage:
    """Tests for complete routing table coverage."""

    @pytest.fixture
    def router(self):
        """Create an AdaptiveRouter instance."""
        from src.layer4_query.routing import AdaptiveRouter
        return AdaptiveRouter()

    def test_routing_table_exists(self, router):
        """Verify routing table is defined."""
        assert hasattr(router, "ROUTING_TABLE") or hasattr(type(router), "ROUTING_TABLE")

    def test_routing_covers_all_query_types(self, router, make_query_plan):
        """All QueryType values should be routable."""
        for query_type in QueryType:
            plan = make_query_plan(
                query_type=query_type,
                complexity_score=0.5,
            )
            decision = router.route(plan)
            # Should not raise, and should return valid decision
            assert decision.min_docs > 0
            assert decision.max_docs >= decision.min_docs
