"""Configuration for Graph Coloring puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class GraphColoringConfig(BaseModel):
    """Configuration for a Graph Coloring puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    num_nodes: int = Field(ge=4, le=20, description="Number of nodes in the graph")
    num_colors: int = Field(ge=2, le=8, description="Number of available colors")
    edge_density: float = Field(ge=0.1, le=0.9, description="Probability of edge between nodes")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "GraphColoringConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_nodes": 6, "num_colors": 3, "edge_density": 0.3},
            DifficultyLevel.MEDIUM: {"num_nodes": 10, "num_colors": 4, "edge_density": 0.4},
            DifficultyLevel.HARD: {"num_nodes": 15, "num_colors": 4, "edge_density": 0.5},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
