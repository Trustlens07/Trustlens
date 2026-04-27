"""Active bias mitigation and debiasing techniques."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DebiasingResult:
    """Result of debiasing operation."""
    original_scores: List[float]
    adjusted_scores: List[float]
    adjustment_details: Dict[str, Any]
    fairness_improvement: float
    method_used: str


class BiasMitigator:
    """
    Active bias mitigation using various algorithmic fairness techniques.
    
    Implements:
    - Demographic Parity adjustment
    - Equal Opportunity balancing
    - Blind resume processing
    - Score calibration
    """
    
    @staticmethod
    def demographic_parity_adjustment(
        scores: List[float],
        protected_attrs: List[str],
        target_parity_threshold: float = 0.9
    ) -> DebiasingResult:
        """
        Adjust scores to ensure demographic parity across groups.
        
        Demographic parity requires that all groups have similar selection rates.
        """
        if len(scores) != len(protected_attrs):
            raise ValueError("Scores and protected_attrs must have same length")
        
        if not scores:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores,
                adjustment_details={},
                fairness_improvement=0.0,
                method_used="none"
            )
        
        # Group scores by protected attribute
        groups = {}
        for score, attr in zip(scores, protected_attrs):
            if attr not in groups:
                groups[attr] = []
            groups[attr].append(score)
        
        # Calculate group statistics
        group_means = {attr: np.mean(group_scores) for attr, group_scores in groups.items()}
        overall_mean = np.mean(scores)
        
        # Calculate current demographic parity ratio
        if len(group_means) >= 2:
            current_parity = min(group_means.values()) / max(group_means.values())
        else:
            current_parity = 1.0
        
        # If already fair enough, no adjustment needed
        if current_parity >= target_parity_threshold:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores.copy(),
                adjustment_details={
                    "current_parity": current_parity,
                    "target_parity": target_parity_threshold,
                    "adjustment_needed": False
                },
                fairness_improvement=0.0,
                method_used="demographic_parity"
            )
        
        # Adjust scores toward overall mean
        adjusted_scores = []
        adjustments = []
        
        for score, attr in zip(scores, protected_attrs):
            group_mean = group_means[attr]
            
            # Calculate adjustment: move score toward overall mean
            # Groups below mean get boosted, groups above get reduced
            difference = overall_mean - group_mean
            adjustment_factor = 0.4  # Moderate adjustment strength
            adjustment = difference * adjustment_factor
            
            new_score = score + adjustment
            # Keep within valid bounds
            new_score = max(0.0, min(100.0, new_score))
            
            adjusted_scores.append(new_score)
            adjustments.append(adjustment)
        
        # Calculate improvement
        new_groups = {}
        for score, attr in zip(adjusted_scores, protected_attrs):
            if attr not in new_groups:
                new_groups[attr] = []
            new_groups[attr].append(score)
        
        new_means = {attr: np.mean(group_scores) for attr, group_scores in new_groups.items()}
        new_parity = min(new_means.values()) / max(new_means.values()) if len(new_means) >= 2 else 1.0
        improvement = new_parity - current_parity
        
        logger.info(
            f"Demographic parity adjustment: {current_parity:.3f} -> {new_parity:.3f} "
            f"(+{improvement:.3f} improvement)"
        )
        
        return DebiasingResult(
            original_scores=scores.copy(),
            adjusted_scores=adjusted_scores,
            adjustment_details={
                "current_parity": round(current_parity, 3),
                "new_parity": round(new_parity, 3),
                "target_parity": target_parity_threshold,
                "adjustment_needed": True,
                "group_means_before": {k: round(v, 2) for k, v in group_means.items()},
                "group_means_after": {k: round(v, 2) for k, v in new_means.items()},
                "max_adjustment": round(max(abs(a) for a in adjustments), 2),
                "adjustments_made": len([a for a in adjustments if abs(a) > 0.01])
            },
            fairness_improvement=round(improvement, 3),
            method_used="demographic_parity"
        )
    
    @staticmethod
    def equal_opportunity_adjustment(
        scores: List[float],
        protected_attrs: List[str],
        true_labels: List[bool],  # Actual qualifications/labels
        target_opportunity_diff: float = 5.0
    ) -> DebiasingResult:
        """
        Adjust scores to ensure equal opportunity across groups.
        
        Equal opportunity requires that qualified candidates have equal 
        chance of selection regardless of protected attributes.
        """
        if len(scores) != len(protected_attrs) or len(scores) != len(true_labels):
            raise ValueError("All input lists must have same length")
        
        if not scores:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores,
                adjustment_details={},
                fairness_improvement=0.0,
                method_used="none"
            )
        
        # Calculate true positive rates (selection of qualified candidates)
        groups_tpr = {}
        for score, attr, qualified in zip(scores, protected_attrs, true_labels):
            if attr not in groups_tpr:
                groups_tpr[attr] = {"selected": 0, "qualified": 0}
            
            if qualified:
                groups_tpr[attr]["qualified"] += 1
                if score >= 70:  # Selection threshold
                    groups_tpr[attr]["selected"] += 1
        
        # Calculate TPR for each group
        tpr_rates = {}
        for attr, counts in groups_tpr.items():
            if counts["qualified"] > 0:
                tpr_rates[attr] = counts["selected"] / counts["qualified"]
            else:
                tpr_rates[attr] = 0.0
        
        if len(tpr_rates) < 2:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores.copy(),
                adjustment_details={"reason": "insufficient_groups"},
                fairness_improvement=0.0,
                method_used="equal_opportunity"
            )
        
        # Check if already fair
        max_tpr = max(tpr_rates.values())
        min_tpr = min(tpr_rates.values())
        current_diff = (max_tpr - min_tpr) * 100  # Convert to score points
        
        if current_diff <= target_opportunity_diff:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores.copy(),
                adjustment_details={
                    "current_opportunity_diff": round(current_diff, 2),
                    "target_diff": target_opportunity_diff,
                    "tpr_rates": {k: round(v, 3) for k, v in tpr_rates.items()},
                    "adjustment_needed": False
                },
                fairness_improvement=0.0,
                method_used="equal_opportunity"
            )
        
        # Adjust scores to balance TPR
        # Find target TPR (average of current rates)
        target_tpr = np.mean(list(tpr_rates.values()))
        
        adjusted_scores = []
        for score, attr, qualified in zip(scores, protected_attrs, true_labels):
            if not qualified:
                # Don't adjust unqualified candidates
                adjusted_scores.append(score)
                continue
            
            current_tpr = tpr_rates[attr]
            tpr_difference = target_tpr - current_tpr
            
            # Convert TPR difference to score adjustment
            # If group is under-selected, boost their scores
            score_adjustment = tpr_difference * 20  # Scale factor
            new_score = score + score_adjustment
            new_score = max(0.0, min(100.0, new_score))
            
            adjusted_scores.append(new_score)
        
        # Calculate new TPR rates
        new_groups_tpr = {}
        for score, attr, qualified in zip(adjusted_scores, protected_attrs, true_labels):
            if not qualified:
                continue
            if attr not in new_groups_tpr:
                new_groups_tpr[attr] = {"selected": 0, "qualified": 0}
            new_groups_tpr[attr]["qualified"] += 1
            if score >= 70:
                new_groups_tpr[attr]["selected"] += 1
        
        new_tpr_rates = {
            attr: counts["selected"] / counts["qualified"] 
            for attr, counts in new_groups_tpr.items()
            if counts["qualified"] > 0
        }
        new_diff = (max(new_tpr_rates.values()) - min(new_tpr_rates.values())) * 100
        improvement = current_diff - new_diff
        
        logger.info(
            f"Equal opportunity adjustment: diff {current_diff:.2f} -> {new_diff:.2f} "
            f"(-{improvement:.2f} improvement)"
        )
        
        return DebiasingResult(
            original_scores=scores.copy(),
            adjusted_scores=adjusted_scores,
            adjustment_details={
                "current_opportunity_diff": round(current_diff, 2),
                "new_opportunity_diff": round(new_diff, 2),
                "tpr_rates_before": {k: round(v, 3) for k, v in tpr_rates.items()},
                "tpr_rates_after": {k: round(v, 3) for k, v in new_tpr_rates.items()},
                "target_tpr": round(target_tpr, 3),
                "adjustment_needed": True
            },
            fairness_improvement=round(improvement / 100, 3),
            method_used="equal_opportunity"
        )
    
    @staticmethod
    def blind_resume_processing(
        parsed_resume: Dict[str, Any],
        blind_level: str = "standard"
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Remove potentially biasing information from resume before scoring.
        
        Levels:
        - "minimal": Remove only obvious identifiers (names)
        - "standard": Remove names, addresses, gender indicators
        - "maximum": Remove all potentially biasing info including school names
        """
        blinded = parsed_resume.copy()
        removed_fields = {}
        
        # Always remove from contact info
        if "contact_info" in blinded:
            contact = blinded["contact_info"]
            
            if "name" in contact:
                removed_fields["name"] = contact["name"]
                contact["name"] = "[REDACTED]"
            
            if "address" in contact:
                removed_fields["address"] = contact["address"]
                contact["address"] = "[REDACTED]"
            
            if "phone" in contact and blind_level in ["standard", "maximum"]:
                removed_fields["phone"] = contact["phone"]
                contact["phone"] = "[REDACTED]"
            
            if "email" in contact:
                # Keep email domain but anonymize username
                email = contact["email"]
                if "@" in email:
                    domain = email.split("@")[1]
                    contact["email"] = f"candidate@{domain}"
                    removed_fields["email"] = email
        
        # Standard level: remove graduation years (age indicators)
        if blind_level in ["standard", "maximum"] and "education" in blinded:
            for edu in blinded["education"]:
                if "graduation_year" in edu:
                    if "graduation_year" not in removed_fields:
                        removed_fields["graduation_year"] = []
                    removed_fields["graduation_year"].append(edu["graduation_year"])
                    edu["graduation_year"] = "[REDACTED]"
        
        # Maximum level: remove school/company names that might indicate background
        if blind_level == "maximum":
            if "education" in blinded:
                for edu in blinded["education"]:
                    if "institution" in edu:
                        if "institution" not in removed_fields:
                            removed_fields["institution"] = []
                        removed_fields["institution"].append(edu["institution"])
                        edu["institution"] = "[REDACTED]"
            
            if "experience" in blinded:
                for exp in blinded["experience"]:
                    if "company" in exp:
                        if "company" not in removed_fields:
                            removed_fields["company"] = []
                        removed_fields["company"].append(exp["company"])
                        exp["company"] = "[REDACTED]"
        
        # Add metadata about blinding
        blinded["_blinding_metadata"] = {
            "level": blind_level,
            "fields_removed": list(removed_fields.keys()),
            "original_data_stored": True
        }
        
        logger.info(f"Resume blinded at level '{blind_level}'. Removed: {list(removed_fields.keys())}")
        
        return blinded, removed_fields
    
    @staticmethod
    def calibrate_scores(
        scores: List[float],
        reference_scores: List[float],
        method: str = "zscore"
    ) -> DebiasingResult:
        """
        Calibrate candidate scores against a reference distribution.
        
        Useful when different scoring models or versions produce different scales.
        """
        if not scores or not reference_scores:
            return DebiasingResult(
                original_scores=scores,
                adjusted_scores=scores,
                adjustment_details={"reason": "insufficient_data"},
                fairness_improvement=0.0,
                method_used="calibration"
            )
        
        if method == "zscore":
            # Z-score normalization
            candidate_mean = np.mean(scores)
            candidate_std = np.std(scores)
            
            reference_mean = np.mean(reference_scores)
            reference_std = np.std(reference_scores)
            
            if candidate_std == 0:
                return DebiasingResult(
                    original_scores=scores,
                    adjusted_scores=scores,
                    adjustment_details={"reason": "zero_variance"},
                    fairness_improvement=0.0,
                    method_used="calibration"
                )
            
            # Convert to z-scores, then to reference scale
            z_scores = [(s - candidate_mean) / candidate_std for s in scores]
            adjusted_scores = [
                max(0.0, min(100.0, (z * reference_std) + reference_mean))
                for z in z_scores
            ]
            
            # Calculate improvement as reduction in variance difference
            new_std = np.std(adjusted_scores)
            original_std_diff = abs(candidate_std - reference_std)
            new_std_diff = abs(new_std - reference_std)
            improvement = (original_std_diff - new_std_diff) / original_std_diff if original_std_diff > 0 else 0.0
            
            return DebiasingResult(
                original_scores=scores.copy(),
                adjusted_scores=adjusted_scores,
                adjustment_details={
                    "method": "zscore",
                    "original_mean": round(candidate_mean, 2),
                    "original_std": round(candidate_std, 2),
                    "reference_mean": round(reference_mean, 2),
                    "reference_std": round(reference_std, 2),
                    "new_mean": round(np.mean(adjusted_scores), 2),
                    "new_std": round(new_std, 2)
                },
                fairness_improvement=round(improvement, 3),
                method_used="calibration"
            )
        
        elif method == "minmax":
            # Min-max scaling to reference range
            candidate_min = min(scores)
            candidate_max = max(scores)
            reference_min = min(reference_scores)
            reference_max = max(reference_scores)
            
            if candidate_max == candidate_min:
                return DebiasingResult(
                    original_scores=scores,
                    adjusted_scores=scores,
                    adjustment_details={"reason": "zero_range"},
                    fairness_improvement=0.0,
                    method_used="calibration"
                )
            
            # Normalize to [0, 1], then scale to reference range
            normalized = [(s - candidate_min) / (candidate_max - candidate_min) for s in scores]
            adjusted_scores = [
                reference_min + n * (reference_max - reference_min)
                for n in normalized
            ]
            
            return DebiasingResult(
                original_scores=scores.copy(),
                adjusted_scores=adjusted_scores,
                adjustment_details={
                    "method": "minmax",
                    "original_range": [round(candidate_min, 2), round(candidate_max, 2)],
                    "reference_range": [round(reference_min, 2), round(reference_max, 2)],
                    "new_range": [round(min(adjusted_scores), 2), round(max(adjusted_scores), 2)]
                },
                fairness_improvement=0.0,  # Min-max preserves distribution shape
                method_used="calibration"
            )
        
        return DebiasingResult(
            original_scores=scores,
            adjusted_scores=scores,
            adjustment_details={"reason": "unknown_method"},
            fairness_improvement=0.0,
            method_used="calibration"
        )


class FairnessPresets:
    """Predefined fairness configurations for different use cases."""
    
    BALANCED = {
        "name": "balanced",
        "description": "Balance between demographic parity and individual merit",
        "demographic_parity_threshold": 0.85,
        "equal_opportunity_threshold": 8.0,
        "blinding_level": "standard",
        "adjustment_strength": 0.4
    }
    
    STRICT = {
        "name": "strict",
        "description": "Maximum fairness enforcement, prioritizing group equity",
        "demographic_parity_threshold": 0.95,
        "equal_opportunity_threshold": 3.0,
        "blinding_level": "maximum",
        "adjustment_strength": 0.7
    }
    
    MINIMAL = {
        "name": "minimal",
        "description": "Minimal intervention, focus on detection only",
        "demographic_parity_threshold": 0.70,
        "equal_opportunity_threshold": 15.0,
        "blinding_level": "minimal",
        "adjustment_strength": 0.2
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Dict[str, Any]:
        """Get a fairness preset by name."""
        presets = {
            "balanced": cls.BALANCED,
            "strict": cls.STRICT,
            "minimal": cls.MINIMAL
        }
        return presets.get(name.lower(), cls.BALANCED)
