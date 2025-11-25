import numpy as np
from collections import defaultdict, Counter
import pandas as pd

class ModelScoringEngine:
    def __init__(self, model_name, responses):
        self.model_name = model_name
        self.responses = responses

    def compute_raw_visibility(self):
        total = len(self.responses)
        mentioned = sum(r["brand_mentioned"] for r in self.responses)
        missing = total - mentioned
        return {
            "total_queries": total,
            "brand_mentioned": mentioned,
            "brand_missing": missing,
            "visibility_percent": round((mentioned / total) * 100, 2) if total else 0
        }

    def compute_category_visibility(self):
        data = defaultdict(lambda: {"total": 0, "mentioned": 0})

        for r in self.responses:
            cat = r["category"]
            data[cat]["total"] += 1
            if r["brand_mentioned"]:
                data[cat]["mentioned"] += 1

        final = {}
        for cat, v in data.items():
            percent = (v["mentioned"] / v["total"]) * 100 if v["total"] else 0
            final[cat] = {"visibility_percent": round(percent, 2)}
        return final

    def compute_competitor_score(self):
        freq = Counter()
        wins = Counter()
        losses = Counter()

        for r in self.responses:
            comps = r["competitors_brand_level"]
            for c in comps:
                freq[c] += 1
                if r["brand_mentioned"]:
                    wins[c] += 1
                else:
                    losses[c] += 1

        out = {}
        for c in freq:
            out[c] = {
                "frequency": freq[c],
                "wins": wins[c],
                "losses": losses[c],
                "win_loss_ratio": round(wins[c] / losses[c], 2) if losses[c] else float("inf")
            }
        return out

    def compute_product_score(self):
        freq = Counter()
        replace = Counter()

        for r in self.responses:
            for p in r["competitors_product_level"]:
                freq[p] += 1
                if not r["brand_mentioned"]:
                    replace[p] += 1

        return {
            "product_frequency": dict(freq.most_common()),
            "product_replaces_brand": dict(replace.most_common())
        }

    def compute_model_level_score(self):
        relevant = [r for r in self.responses if r["category"] in ("comparison", "best_of", "budget")]

        recall = (sum(r["brand_mentioned"] for r in relevant) / max(len(relevant), 1)) * 100
        ranking_quality = 85  # placeholder since ranks missing
        coverage = np.mean([self.compute_category_visibility()[k]["visibility_percent"]
                            for k in self.compute_category_visibility()])
        bias = 30
        hallucination = 100
        fairness = min(100, recall * 1.2)

        final = (
            0.25 * recall +
            0.20 * ranking_quality +
            0.20 * coverage +
            0.15 * (100 - bias) +
            0.10 * hallucination +
            0.10 * fairness
        )

        return {
            "recall": round(recall, 2),
            "ranking_quality": ranking_quality,
            "coverage": round(coverage, 2),
            "bias": bias,
            "hallucination_score": hallucination,
            "fairness": round(fairness, 2),
            "final_model_score": round(final, 2)
        }

    def run(self):
        return {
            "model_name": self.model_name,
            "raw_visibility": self.compute_raw_visibility(),
            "category_visibility": self.compute_category_visibility(),
            "competitor_score": self.compute_competitor_score(),
            "product_score": self.compute_product_score(),
            "model_level_score": self.compute_model_level_score()
        }


class MultiModelScoringEngine:
    def __init__(self, flat_data):
        self.flat_data = flat_data

    def run(self):
        df = pd.DataFrame(self.flat_data)
        results = {}
        for model, group in df.groupby("model_name"):
            engine = ModelScoringEngine(model, group.to_dict(orient="records"))
            results[model] = engine.run()
        return results