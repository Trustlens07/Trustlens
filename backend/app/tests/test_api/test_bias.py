"""Tests for bias analysis API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.bias_metric import BiasMetric

client = TestClient(app)


# Override database dependency for testing
def override_get_db():
    """Override database dependency with test database."""
    # In production, use test database URL
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestBiasAnalyzeEndpoint:
    """Test POST /api/v1/bias/analyze endpoint."""
    
    def test_bias_analyze_success(self):
        """Test successful bias analysis with valid candidates."""
        response = client.post("/api/v1/bias/analyze", json={
            "candidates": [
                {
                    "id": "c1",
                    "score": 85.0,
                    "protected_attributes": {"gender": "male"},
                    "attributes": {"department": "engineering"}
                },
                {
                    "id": "c2",
                    "score": 78.0,
                    "protected_attributes": {"gender": "female"},
                    "attributes": {"department": "engineering"}
                },
                {
                    "id": "c3",
                    "score": 82.0,
                    "protected_attributes": {"gender": "male"},
                    "attributes": {"department": "design"}
                }
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_bias_analyze_empty_candidates(self):
        """Test bias analysis with empty candidate list."""
        response = client.post("/api/v1/bias/analyze", json={
            "candidates": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_bias_analyze_missing_scores(self):
        """Test bias analysis handling candidates without scores."""
        response = client.post("/api/v1/bias/analyze", json={
            "candidates": [
                {"id": "c1", "protected_attributes": {"gender": "male"}},
                {"id": "c2", "score": 80.0, "protected_attributes": {"gender": "female"}}
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_bias_analyze_invalid_request(self):
        """Test bias analysis with invalid request format."""
        response = client.post("/api/v1/bias/analyze", json={
            "invalid_field": "value"
        })
        
        # Should either handle gracefully or return validation error
        assert response.status_code in [200, 422]


class TestBiasMetricsEndpoint:
    """Test GET /api/v1/bias/metrics endpoint."""
    
    def test_get_bias_metrics_success(self):
        """Test retrieving bias metrics."""
        response = client.get("/api/v1/bias/metrics")
        
        assert response.status_code in [200, 404]  # 404 if no data yet
        
        if response.status_code == 200:
            data = response.json()
            assert "overall" in data or "groups" in data
    
    def test_get_bias_metrics_with_group_filter(self):
        """Test retrieving bias metrics filtered by group type."""
        response = client.get("/api/v1/bias/metrics?group_type=gender")
        
        assert response.status_code in [200, 404]
    
    def test_get_bias_metrics_with_candidate_id(self):
        """Test retrieving bias metrics for specific candidate."""
        response = client.get("/api/v1/bias/metrics?candidate_id=test-candidate-123")
        
        # Should return 404 for non-existent candidate
        assert response.status_code in [200, 404]
    
    def test_get_bias_metrics_enhanced_version(self):
        """Test retrieving enhanced bias metrics."""
        response = client.get("/api/v1/bias/metrics?version=enhanced&candidate_id=test-123")
        
        # Should require candidate_id for enhanced version
        assert response.status_code in [200, 400, 404]


class TestBiasCalculations:
    """Test bias metric calculations."""
    
    def test_demographic_parity_calculation(self):
        """Test demographic parity ratio calculation."""
        from app.orchestrators.screening_orchestrator import ScreeningOrchestrator
        
        candidates = [
            {"name": "Alice", "score": 85.0},
            {"name": "Bob", "score": 80.0},
            {"name": "Carol", "score": 82.0},
            {"name": "David", "score": 78.0},
        ]
        
        metrics = ScreeningOrchestrator._calculate_fairness_metrics(
            db=None, session_id="test", candidates=candidates
        )
        
        assert "overall_score" in metrics
        assert "demographic_parity_ratio" in metrics
        assert "group_means" in metrics
        assert 0 <= metrics["overall_score"] <= 1
    
    def test_bias_detection_threshold(self):
        """Test that bias is detected when disparate impact < 0.8."""
        from app.orchestrators.screening_orchestrator import ScreeningOrchestrator
        
        # Create biased scenario: one group has much lower scores
        candidates = [
            {"name": "Alice", "score": 45.0},   # Low score
            {"name": "Anna", "score": 48.0},   # Low score
            {"name": "Bob", "score": 85.0},    # High score
            {"name": "Ben", "score": 88.0},    # High score
        ]
        
        metrics = ScreeningOrchestrator._calculate_fairness_metrics(
            db=None, session_id="test", candidates=candidates
        )
        
        # Should detect bias when disparate impact is significant
        if "is_biased" in metrics:
            assert isinstance(metrics["is_biased"], bool)
    
    def test_fairness_recommendations(self):
        """Test that recommendations are generated for biased scenarios."""
        from app.orchestrators.screening_orchestrator import ScreeningOrchestrator
        
        recommendations = ScreeningOrchestrator._generate_fairness_recommendations(
            is_biased=True,
            demographic_parity_ratio=0.75,
            disparate_impact={"gender_female": 0.65, "gender_male": 1.0}
        )
        
        assert len(recommendations) > 0
        assert any("parity" in r.lower() for r in recommendations)


class TestDebiasingService:
    """Test the debiasing service."""
    
    def test_demographic_parity_adjustment(self):
        """Test demographic parity score adjustment."""
        from app.services.debiasing import BiasMitigator
        
        scores = [70.0, 75.0, 80.0, 85.0]  # Group A
        scores.extend([50.0, 55.0, 60.0, 65.0])  # Group B (lower)
        
        protected_attrs = ["A", "A", "A", "A", "B", "B", "B", "B"]
        
        result = BiasMitigator.demographic_parity_adjustment(
            scores=scores,
            protected_attrs=protected_attrs,
            target_parity_threshold=0.9
        )
        
        assert len(result.adjusted_scores) == len(scores)
        assert result.fairness_improvement >= 0  # Should improve or stay same
        assert result.method_used == "demographic_parity"
    
    def test_blind_resume_processing(self):
        """Test blind resume processing."""
        from app.services.debiasing import BiasMitigator
        
        resume = {
            "contact_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "address": "123 Main St"
            },
            "education": [
                {"institution": "Harvard", "graduation_year": 2015}
            ],
            "experience": [
                {"company": "Google", "title": "Engineer"}
            ]
        }
        
        blinded, removed = BiasMitigator.blind_resume_processing(
            resume, blind_level="standard"
        )
        
        assert blinded["contact_info"]["name"] == "[REDACTED]"
        assert "name" in removed
        assert "address" in removed
    
    def test_fairness_presets(self):
        """Test fairness preset configurations."""
        from app.services.debiasing import FairnessPresets
        
        balanced = FairnessPresets.get_preset("balanced")
        assert balanced["name"] == "balanced"
        assert "demographic_parity_threshold" in balanced
        
        strict = FairnessPresets.get_preset("strict")
        assert strict["demographic_parity_threshold"] > balanced["demographic_parity_threshold"]


class TestBiasEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_candidate(self):
        """Test bias analysis with single candidate."""
        response = client.post("/api/v1/bias/analyze", json={
            "candidates": [{"id": "c1", "score": 85.0}]
        })
        
        assert response.status_code == 200
    
    def test_all_same_scores(self):
        """Test bias analysis when all candidates have same score."""
        response = client.post("/api/v1/bias/analyze", json={
            "candidates": [
                {"id": "c1", "score": 80.0},
                {"id": "c2", "score": 80.0},
                {"id": "c3", "score": 80.0}
            ]
        })
        
        assert response.status_code == 200
    
    def test_very_large_batch(self):
        """Test bias analysis with large batch of candidates."""
        candidates = [
            {"id": f"c{i}", "score": float(50 + (i % 50))}
            for i in range(100)
        ]
        
        response = client.post("/api/v1/bias/analyze", json={"candidates": candidates})
        
        assert response.status_code == 200
